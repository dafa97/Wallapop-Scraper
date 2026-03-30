import json
import pytest
from src.database import (
    parse_price,
    upsert_item,
    get_items,
    get_item_by_id,
    get_opportunities,
    get_stats,
    save_items_to_db,
)


# ── parse_price ──────────────────────────────────────────────────────────────

def test_parse_price_entero_simple():
    assert parse_price("12€") == 12.0


def test_parse_price_decimal_coma():
    assert parse_price("12,50€") == 12.5


def test_parse_price_miles():
    assert parse_price("1.200€") == 1200.0


def test_parse_price_miles_con_decimal():
    assert parse_price("1.200,50€") == 1200.5


def test_parse_price_unicode_euro():
    assert parse_price("99\u20ac") == 99.0


def test_parse_price_grande():
    assert parse_price("10.500,99€") == 10500.99


def test_parse_price_cero():
    assert parse_price("0€") == 0.0


def test_parse_price_gratis():
    assert parse_price("Gratis") is None


def test_parse_price_no_disponible():
    assert parse_price("No disponible") is None


def test_parse_price_none():
    assert parse_price(None) is None


def test_parse_price_cadena_vacia():
    assert parse_price("") is None


def test_parse_price_espacios():
    assert parse_price("  ") is None


# ── upsert_item ──────────────────────────────────────────────────────────────

ITEM_BASE = {
    "url": "https://www.wallapop.com/item/abc123",
    "title": "MacBook Pro M1",
    "price": "800€",
    "description": "Buen estado",
    "location": "Madrid",
}


def test_upsert_item_insert_nuevo(db_path):
    upsert_item(ITEM_BASE, "macbook")
    result = get_items()
    assert result["total"] == 1
    item = result["items"][0]
    assert item["title"] == "MacBook Pro M1"
    assert item["price"] == 800.0
    assert item["query"] == "macbook"


def test_upsert_item_price_history_inicial(db_path):
    upsert_item(ITEM_BASE, "macbook")
    item = get_items()["items"][0]
    history = json.loads(item["price_history"])
    assert len(history) == 1
    assert history[0]["price"] == 800.0


def test_upsert_item_sin_precio(db_path):
    item = {**ITEM_BASE, "price": None}
    upsert_item(item, "macbook")
    row = get_items()["items"][0]
    assert row["price"] is None
    assert json.loads(row["price_history"]) == []


def test_upsert_item_update_mismo_precio(db_path):
    upsert_item(ITEM_BASE, "macbook")
    first_seen_before = get_items()["items"][0]["first_seen"]

    upsert_item(ITEM_BASE, "macbook")

    row = get_items()["items"][0]
    assert row["first_seen"] == first_seen_before
    assert len(json.loads(row["price_history"])) == 1


def test_upsert_item_update_precio_distinto(db_path):
    upsert_item(ITEM_BASE, "macbook")

    item_nuevo_precio = {**ITEM_BASE, "price": "700€"}
    upsert_item(item_nuevo_precio, "macbook")

    row = get_items()["items"][0]
    assert row["price"] == 700.0
    history = json.loads(row["price_history"])
    assert len(history) == 2
    assert history[1]["price"] == 700.0


def test_upsert_item_first_seen_no_cambia_en_update(db_path):
    upsert_item(ITEM_BASE, "macbook")
    first_seen = get_items()["items"][0]["first_seen"]

    item_mod = {**ITEM_BASE, "title": "Título nuevo", "price": "900€"}
    upsert_item(item_mod, "macbook")

    assert get_items()["items"][0]["first_seen"] == first_seen


def test_upsert_item_acumula_tres_cambios_de_precio(db_path):
    upsert_item(ITEM_BASE, "macbook")
    upsert_item({**ITEM_BASE, "price": "750€"}, "macbook")
    upsert_item({**ITEM_BASE, "price": "700€"}, "macbook")

    history = json.loads(get_items()["items"][0]["price_history"])
    assert len(history) == 3


# ── get_items ────────────────────────────────────────────────────────────────

def _insertar_items(items_list, query="test"):
    for item in items_list:
        upsert_item(item, query)


def test_get_items_db_vacia(db_path):
    result = get_items()
    assert result == {"items": [], "total": 0}


def test_get_items_devuelve_todos(db_path):
    _insertar_items([
        {**ITEM_BASE, "url": "https://wallapop.com/item/1", "title": "Item A", "price": "100€"},
        {**ITEM_BASE, "url": "https://wallapop.com/item/2", "title": "Item B", "price": "200€"},
    ])
    result = get_items()
    assert result["total"] == 2
    assert len(result["items"]) == 2


def test_get_items_filtro_query_title(db_path):
    _insertar_items([
        {**ITEM_BASE, "url": "https://wallapop.com/item/1", "title": "MacBook Pro"},
        {**ITEM_BASE, "url": "https://wallapop.com/item/2", "title": "iPhone 14"},
    ])
    result = get_items(query="macbook")
    assert result["total"] == 1
    assert result["items"][0]["title"] == "MacBook Pro"


def test_get_items_filtro_max_price(db_path):
    _insertar_items([
        {**ITEM_BASE, "url": "https://wallapop.com/item/1", "title": "A", "price": "50€"},
        {**ITEM_BASE, "url": "https://wallapop.com/item/2", "title": "B", "price": "100€"},
        {**ITEM_BASE, "url": "https://wallapop.com/item/3", "title": "C", "price": "150€"},
    ])
    result = get_items(max_price=100)
    assert result["total"] == 2


def test_get_items_sort_price_asc(db_path):
    _insertar_items([
        {**ITEM_BASE, "url": "https://wallapop.com/item/1", "title": "A", "price": "300€"},
        {**ITEM_BASE, "url": "https://wallapop.com/item/2", "title": "B", "price": "100€"},
        {**ITEM_BASE, "url": "https://wallapop.com/item/3", "title": "C", "price": "200€"},
    ])
    items = get_items(sort="price_asc")["items"]
    prices = [i["price"] for i in items]
    assert prices == sorted(prices)


def test_get_items_sort_price_desc(db_path):
    _insertar_items([
        {**ITEM_BASE, "url": "https://wallapop.com/item/1", "title": "A", "price": "100€"},
        {**ITEM_BASE, "url": "https://wallapop.com/item/2", "title": "B", "price": "300€"},
    ])
    items = get_items(sort="price_desc")["items"]
    prices = [i["price"] for i in items]
    assert prices == sorted(prices, reverse=True)


def test_get_items_paginacion(db_path):
    for i in range(10):
        upsert_item(
            {**ITEM_BASE, "url": f"https://wallapop.com/item/{i}", "title": f"Item {i}", "price": f"{i*10}€"},
            "test"
        )
    result = get_items(limit=3, offset=0)
    assert len(result["items"]) == 3
    assert result["total"] == 10

    result2 = get_items(limit=3, offset=9)
    assert len(result2["items"]) == 1


def test_get_items_sort_invalido_usa_reciente(db_path):
    _insertar_items([
        {**ITEM_BASE, "url": "https://wallapop.com/item/1", "title": "A", "price": "100€"},
    ])
    # No debe lanzar excepción con sort inválido
    result = get_items(sort="invalido")
    assert result["total"] == 1


# ── get_opportunities ────────────────────────────────────────────────────────

def _insertar_oportunidades(db_path):
    """Inserta 5 items con la misma query a precios distintos."""
    precios = [100, 120, 130, 140, 150]
    for i, precio in enumerate(precios):
        upsert_item(
            {
                "url": f"https://wallapop.com/item/op{i}",
                "title": f"MacBook {i}",
                "price": f"{precio}€",
                "description": "desc",
                "location": "Madrid",
            },
            "macbook"
        )


def test_get_opportunities_db_vacia(db_path):
    result = get_opportunities()
    assert result == {"items": [], "total": 0}


def test_get_opportunities_insuficientes_items(db_path):
    # Solo 2 items: COUNT < 3, no activa la subquery
    for i in range(2):
        upsert_item(
            {**ITEM_BASE, "url": f"https://wallapop.com/item/{i}", "price": "100€"},
            "macbook"
        )
    result = get_opportunities()
    assert result["total"] == 0


def test_get_opportunities_detecta_descuentos(db_path):
    _insertar_oportunidades(db_path)
    # avg = (100+120+130+140+150)/5 = 128
    # items < 128: los de 100 y 120
    result = get_opportunities()
    assert result["total"] == 2
    precios = [i["price"] for i in result["items"]]
    assert all(p < 128 for p in precios)


def test_get_opportunities_discount_pct(db_path):
    _insertar_oportunidades(db_path)
    items = get_opportunities()["items"]
    for item in items:
        assert "discount_pct" in item
        assert item["discount_pct"] > 0


def test_get_opportunities_min_discount(db_path):
    _insertar_oportunidades(db_path)
    # avg ~128; item a 120 tiene descuento ~6%; item a 100 tiene ~22%
    result = get_opportunities(min_discount=20)
    assert result["total"] == 1
    assert result["items"][0]["price"] == 100.0


def test_get_opportunities_excluye_precio_cero(db_path):
    # Insertar item con precio 0
    upsert_item({**ITEM_BASE, "url": "https://wallapop.com/item/zero", "price": "0€"}, "macbook")
    # Más items para llegar al mínimo de 3
    for i in range(4):
        upsert_item(
            {**ITEM_BASE, "url": f"https://wallapop.com/item/x{i}", "price": "100€"},
            "macbook"
        )
    items_result = get_opportunities()["items"]
    assert all(i["price"] > 0 for i in items_result)


# ── get_stats ────────────────────────────────────────────────────────────────

def test_get_stats_db_vacia(db_path):
    stats = get_stats()
    assert stats["total_items"] == 0
    assert stats["unique_queries"] == 0
    assert stats["last_update"] is None
    assert stats["queries"] == []


def test_get_stats_con_datos(db_path):
    upsert_item({**ITEM_BASE, "url": "https://wallapop.com/item/1"}, "macbook")
    upsert_item({**ITEM_BASE, "url": "https://wallapop.com/item/2"}, "macbook")
    upsert_item({**ITEM_BASE, "url": "https://wallapop.com/item/3"}, "iphone")

    stats = get_stats()
    assert stats["total_items"] == 3
    assert stats["unique_queries"] == 2
    assert stats["last_update"] is not None
    queries = {q["query"]: q["count"] for q in stats["queries"]}
    assert queries["macbook"] == 2
    assert queries["iphone"] == 1


def test_get_stats_queries_orden_desc(db_path):
    for i in range(3):
        upsert_item({**ITEM_BASE, "url": f"https://wallapop.com/item/a{i}"}, "macbook")
    upsert_item({**ITEM_BASE, "url": "https://wallapop.com/item/b1"}, "iphone")

    stats = get_stats()
    counts = [q["count"] for q in stats["queries"]]
    assert counts == sorted(counts, reverse=True)


# ── save_items_to_db ─────────────────────────────────────────────────────────

def test_save_items_to_db_guarda_todos(db_path):
    items = [
        {**ITEM_BASE, "url": "https://wallapop.com/item/1"},
        {**ITEM_BASE, "url": "https://wallapop.com/item/2"},
    ]
    saved = save_items_to_db(items, "macbook")
    assert saved == 2
    assert get_items()["total"] == 2


def test_save_items_to_db_lista_vacia(db_path):
    saved = save_items_to_db([], "macbook")
    assert saved == 0
