import json
import pytest
from src.database import upsert_item


# ── Helpers ──────────────────────────────────────────────────────────────────

ITEM_BASE = {
    "url": "https://www.wallapop.com/item/test1",
    "title": "MacBook Pro M1",
    "price": "800€",
    "description": "Buen estado",
    "location": "Madrid",
}


def insertar_item(db_path, url_suffix="test1", title="MacBook Pro M1",
                  price="800€", query="macbook"):
    item = {**ITEM_BASE, "url": f"https://www.wallapop.com/item/{url_suffix}",
            "title": title, "price": price}
    upsert_item(item, query)


# ── GET /api/items ───────────────────────────────────────────────────────────

def test_list_items_db_vacia(api_client):
    resp = api_client.get("/api/items")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_items_con_datos(api_client, db_path):
    insertar_item(db_path)
    resp = api_client.get("/api/items")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_list_items_price_history_es_lista(api_client, db_path):
    insertar_item(db_path)
    resp = api_client.get("/api/items")
    item = resp.json()["items"][0]
    assert isinstance(item["price_history"], list)


def test_list_items_filtro_query(api_client, db_path):
    insertar_item(db_path, "1", "MacBook Pro")
    insertar_item(db_path, "2", "iPhone 14", query="iphone")
    resp = api_client.get("/api/items?query=macbook")
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["title"] == "MacBook Pro"


def test_list_items_filtro_max_price(api_client, db_path):
    insertar_item(db_path, "1", "Barato", "50€")
    insertar_item(db_path, "2", "Caro", "500€")
    resp = api_client.get("/api/items?max_price=100")
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["title"] == "Barato"


def test_list_items_sort_price_asc(api_client, db_path):
    insertar_item(db_path, "1", "A", "300€")
    insertar_item(db_path, "2", "B", "100€")
    insertar_item(db_path, "3", "C", "200€")
    resp = api_client.get("/api/items?sort=price_asc")
    prices = [i["price"] for i in resp.json()["items"]]
    assert prices == sorted(prices)


def test_list_items_paginacion(api_client, db_path):
    for i in range(5):
        upsert_item(
            {**ITEM_BASE, "url": f"https://wallapop.com/item/{i}", "title": f"Item {i}"},
            "test"
        )
    resp = api_client.get("/api/items?limit=2&offset=0")
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5


def test_list_items_limit_invalido(api_client):
    resp = api_client.get("/api/items?limit=0")
    assert resp.status_code == 422


# ── GET /api/items/{item_id} ─────────────────────────────────────────────────

def test_get_item_existente(api_client, db_path):
    insertar_item(db_path)
    item_id = api_client.get("/api/items").json()["items"][0]["id"]
    resp = api_client.get(f"/api/items/{item_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "MacBook Pro M1"


def test_get_item_inexistente_404(api_client, db_path):
    resp = api_client.get("/api/items/9999")
    assert resp.status_code == 404


def test_get_item_price_history_es_lista(api_client, db_path):
    insertar_item(db_path)
    item_id = api_client.get("/api/items").json()["items"][0]["id"]
    resp = api_client.get(f"/api/items/{item_id}")
    assert isinstance(resp.json()["price_history"], list)


# ── GET /api/searches ────────────────────────────────────────────────────────

def test_list_searches_vacio(api_client):
    resp = api_client.get("/api/searches")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_searches_con_datos(api_client, searches_file):
    searches_file.write_text(
        json.dumps({"searches": [{"query": "MacBook", "interval_minutes": 60}]}),
        encoding="utf-8"
    )
    resp = api_client.get("/api/searches")
    assert len(resp.json()) == 1
    assert resp.json()[0]["query"] == "MacBook"


# ── POST /api/searches ───────────────────────────────────────────────────────

def test_add_search_crea_entrada(api_client):
    resp = api_client.post("/api/searches", json={"query": "iPhone", "interval_minutes": 30})
    assert resp.status_code == 201
    assert resp.json()["query"] == "iPhone"


def test_add_search_duplicado_409(api_client):
    api_client.post("/api/searches", json={"query": "MacBook", "interval_minutes": 60})
    resp = api_client.post("/api/searches", json={"query": "MacBook", "interval_minutes": 60})
    assert resp.status_code == 409


def test_add_search_duplicado_case_insensitive(api_client):
    api_client.post("/api/searches", json={"query": "macbook", "interval_minutes": 60})
    resp = api_client.post("/api/searches", json={"query": "MACBOOK", "interval_minutes": 60})
    assert resp.status_code == 409


def test_add_search_falta_campo_query(api_client):
    resp = api_client.post("/api/searches", json={"interval_minutes": 30})
    assert resp.status_code == 422


# ── DELETE /api/searches/{query} ─────────────────────────────────────────────

def test_delete_search_existente(api_client):
    api_client.post("/api/searches", json={"query": "MacBook", "interval_minutes": 60})
    resp = api_client.delete("/api/searches/MacBook")
    assert resp.status_code == 200
    assert api_client.get("/api/searches").json() == []


def test_delete_search_inexistente_404(api_client):
    resp = api_client.delete("/api/searches/NoExiste")
    assert resp.status_code == 404


def test_delete_search_case_insensitive(api_client):
    api_client.post("/api/searches", json={"query": "macbook", "interval_minutes": 60})
    resp = api_client.delete("/api/searches/MACBOOK")
    assert resp.status_code == 200


# ── POST /api/scrape ─────────────────────────────────────────────────────────

def test_force_scrape_query_vacia(api_client):
    resp = api_client.post("/api/scrape", json={"query": "   "})
    assert resp.status_code == 400


def test_force_scrape_inicia_ok(api_client, mocker):
    mocker.patch("src.api.WallapopScraper")
    resp = api_client.post("/api/scrape", json={"query": "MacBook"})
    assert resp.status_code == 200
    assert resp.json()["query"] == "MacBook"


def test_force_scrape_duplicado_409(api_client, mocker):
    import src.events as ev
    ev.start_scrape("MacBook")
    resp = api_client.post("/api/scrape", json={"query": "MacBook"})
    assert resp.status_code == 409


# ── GET /api/scrape/status ────────────────────────────────────────────────────

def test_scrape_status_sin_activos(api_client):
    resp = api_client.get("/api/scrape/status")
    assert resp.status_code == 200
    assert resp.json() == {"active": []}


def test_scrape_status_con_activo(api_client):
    import src.events as ev
    ev.start_scrape("MacBook")
    resp = api_client.get("/api/scrape/status")
    assert "MacBook" in resp.json()["active"]


# ── GET /api/opportunities ────────────────────────────────────────────────────

def test_opportunities_db_vacia(api_client):
    resp = api_client.get("/api/opportunities")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_opportunities_con_datos(api_client, db_path):
    precios = [100, 120, 130, 140, 150]
    for i, p in enumerate(precios):
        upsert_item(
            {**ITEM_BASE, "url": f"https://wallapop.com/item/op{i}", "price": f"{p}€"},
            "macbook"
        )
    resp = api_client.get("/api/opportunities")
    assert resp.status_code == 200
    assert resp.json()["total"] > 0


def test_opportunities_min_discount(api_client, db_path):
    precios = [100, 120, 130, 140, 150]
    for i, p in enumerate(precios):
        upsert_item(
            {**ITEM_BASE, "url": f"https://wallapop.com/item/op{i}", "price": f"{p}€"},
            "macbook"
        )
    # Con descuento mínimo alto, solo el item más barato califica
    resp = api_client.get("/api/opportunities?min_discount=20")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["price"] == 100.0


# ── GET /api/stats ────────────────────────────────────────────────────────────

def test_stats_db_vacia(api_client):
    resp = api_client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_items"] == 0
    assert data["unique_queries"] == 0
    assert data["queries"] == []


def test_stats_con_datos(api_client, db_path):
    insertar_item(db_path, "1", query="macbook")
    insertar_item(db_path, "2", query="macbook")
    insertar_item(db_path, "3", query="iphone")
    resp = api_client.get("/api/stats")
    data = resp.json()
    assert data["total_items"] == 3
    assert data["unique_queries"] == 2
