import json
import os
import logging
import threading
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from src.database import get_items, get_item_by_id, get_stats
from src.scraper import WallapopScraper

app = FastAPI(title="Wallapop Scraper API")

app.mount("/static", StaticFiles(directory="static"), name="static")

SEARCHES_FILE = "searches.json"


@app.get("/")
def root():
    return FileResponse("static/index.html")


def _load_searches():
    """Carga las búsquedas desde searches.json."""
    if not os.path.exists(SEARCHES_FILE):
        return {"searches": []}
    try:
        with open(SEARCHES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"searches": []}


def _save_searches(data):
    """Guarda las búsquedas en searches.json."""
    with open(SEARCHES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _parse_price_history(item):
    """Parsea el campo price_history de string JSON a lista."""
    if item and "price_history" in item:
        ph = item["price_history"]
        if isinstance(ph, str):
            try:
                item["price_history"] = json.loads(ph)
            except (json.JSONDecodeError, TypeError):
                item["price_history"] = []
    return item


# --- Modelos Pydantic ---

class SearchCreate(BaseModel):
    query: str
    interval_minutes: int = 60


class ScrapeRequest(BaseModel):
    query: str
    max_items: Optional[int] = None


# Track de scrapes en curso
_active_scrapes: dict[str, bool] = {}


# --- Endpoints ---

@app.get("/api/items")
def list_items(
    query: Optional[str] = Query(None, description="Búsqueda en título"),
    sort: Optional[str] = Query("recent", description="Orden: price_asc, price_desc, recent"),
    max_price: Optional[float] = Query(None, description="Precio máximo"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Listar items con filtros opcionales."""
    items = get_items(query=query, sort=sort, max_price=max_price, limit=limit, offset=offset)
    return [_parse_price_history(item) for item in items]


@app.get("/api/items/{item_id}")
def get_item_detail(item_id: int):
    """Detalle de un item con historial de precios."""
    item = get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return _parse_price_history(item)


@app.get("/api/searches")
def list_searches():
    """Listar búsquedas activas."""
    data = _load_searches()
    return data["searches"]


@app.post("/api/searches", status_code=201)
def add_search(search: SearchCreate):
    """Añadir nueva búsqueda."""
    data = _load_searches()

    # Verificar si ya existe
    for s in data["searches"]:
        if s["query"].lower() == search.query.lower():
            raise HTTPException(status_code=409, detail="La búsqueda ya existe")

    data["searches"].append({
        "query": search.query,
        "interval_minutes": search.interval_minutes,
    })
    _save_searches(data)
    return {"message": "Búsqueda añadida", "query": search.query}


@app.delete("/api/searches/{query}")
def delete_search(query: str):
    """Eliminar una búsqueda activa."""
    data = _load_searches()
    original_len = len(data["searches"])
    data["searches"] = [s for s in data["searches"] if s["query"].lower() != query.lower()]

    if len(data["searches"]) == original_len:
        raise HTTPException(status_code=404, detail="Búsqueda no encontrada")

    _save_searches(data)
    return {"message": "Búsqueda eliminada", "query": query}


@app.post("/api/scrape")
def force_scrape(req: ScrapeRequest):
    """Forzar un scrape inmediato en background."""
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query vacía")

    if _active_scrapes.get(query):
        raise HTTPException(status_code=409, detail=f"Ya hay un scrape en curso para '{query}'")

    def _run():
        _active_scrapes[query] = True
        try:
            scraper = WallapopScraper(headless=True)
            scraper.run(query, max_items=req.max_items)
        except Exception as e:
            logging.error(f"Error en scrape forzado '{query}': {e}")
        finally:
            _active_scrapes[query] = False

    threading.Thread(target=_run, daemon=True).start()
    return {"message": f"Scrape iniciado para '{query}'", "query": query}


@app.get("/api/scrape/status")
def scrape_status():
    """Ver qué scrapes están en curso."""
    return {"active": [q for q, running in _active_scrapes.items() if running]}


@app.get("/api/stats")
def stats():
    """Resumen general: total items, última ejecución, etc."""
    return get_stats()
