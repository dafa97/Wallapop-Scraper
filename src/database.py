import os
import json
import sqlite3
import logging
from datetime import datetime

DB_DIR = "data"
DB_NAME = "wallapop.db"


def get_db_path():
    os.makedirs(DB_DIR, exist_ok=True)
    return os.path.join(DB_DIR, DB_NAME)


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Crea la tabla items si no existe."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallapop_url TEXT UNIQUE NOT NULL,
            title TEXT,
            price REAL,
            description TEXT,
            location TEXT,
            query TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            price_history TEXT NOT NULL DEFAULT '[]'
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_items_query ON items(query)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_items_price ON items(price)
    """)
    conn.commit()
    conn.close()
    logging.info("Base de datos inicializada.")


def parse_price(price_str):
    """Convierte texto de precio ('12,50\u20ac', '1.200\u20ac') a float."""
    if not price_str or price_str == "No disponible":
        return None
    try:
        cleaned = price_str.replace("€", "").replace("\u20ac", "").strip()
        # Formato español: 1.200,50 -> 1200.50
        cleaned = cleaned.replace(".", "").replace(",", ".")
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def upsert_item(item, query):
    """Inserta o actualiza un item en la DB.

    Si el item (por URL) ya existe:
    - Actualiza last_seen
    - Si el precio cambió, lo añade al historial

    Args:
        item: dict con keys url, title, price, description, location
        query: string de búsqueda que encontró este item
    """
    conn = get_connection()
    now = datetime.now().isoformat()
    price = parse_price(item.get('price', ''))

    existing = conn.execute(
        "SELECT id, price, price_history FROM items WHERE wallapop_url = ?",
        (item['url'],)
    ).fetchone()

    if existing:
        history = json.loads(existing['price_history'])
        old_price = existing['price']

        # Si el precio cambió, añadir al historial
        if price is not None and old_price != price:
            history.append({"price": price, "date": now})
            logging.info(f"Precio actualizado: {old_price} -> {price} | {item.get('title', '')[:40]}")

        conn.execute("""
            UPDATE items SET
                title = ?, price = ?, description = ?, location = ?,
                last_seen = ?, price_history = ?
            WHERE id = ?
        """, (
            item.get('title', 'No disponible'),
            price,
            item.get('description', 'No disponible'),
            item.get('location', 'No disponible'),
            now,
            json.dumps(history),
            existing['id']
        ))
    else:
        initial_history = []
        if price is not None:
            initial_history.append({"price": price, "date": now})

        conn.execute("""
            INSERT INTO items (wallapop_url, title, price, description, location,
                               query, first_seen, last_seen, price_history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item['url'],
            item.get('title', 'No disponible'),
            price,
            item.get('description', 'No disponible'),
            item.get('location', 'No disponible'),
            query,
            now, now,
            json.dumps(initial_history)
        ))

    conn.commit()
    conn.close()


def save_items_to_db(items, query):
    """Guarda una lista de items en la DB."""
    init_db()
    saved = 0
    for item in items:
        try:
            upsert_item(item, query)
            saved += 1
        except Exception as e:
            logging.error(f"Error guardando item {item.get('url', '?')}: {e}")
    logging.info(f"[DB] {saved}/{len(items)} items guardados para query '{query}'")
    return saved


def get_items(query=None, sort="recent", max_price=None, limit=50, offset=0):
    """Consulta items con filtros.

    Args:
        query: filtro por texto en título (LIKE)
        sort: price_asc, price_desc, recent
        max_price: precio máximo
        limit: máximo de resultados
        offset: paginación
    """
    conn = get_connection()
    sql = "SELECT * FROM items WHERE 1=1"
    params = []

    if query:
        sql += " AND title LIKE ?"
        params.append(f"%{query}%")

    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)

    # Contar total antes de paginar
    count_sql = sql.replace("SELECT *", "SELECT COUNT(*)", 1)
    total = conn.execute(count_sql, params).fetchone()[0]

    order_map = {
        "price_asc": "price ASC",
        "price_desc": "price DESC",
        "recent": "last_seen DESC",
    }
    sql += f" ORDER BY {order_map.get(sort, 'last_seen DESC')}"
    sql += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return {"items": [dict(row) for row in rows], "total": total}


def get_item_by_id(item_id):
    """Obtiene un item por su ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_stats():
    """Resumen general de la DB."""
    conn = get_connection()
    stats = {}
    stats['total_items'] = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    stats['unique_queries'] = conn.execute("SELECT COUNT(DISTINCT query) FROM items").fetchone()[0]

    last = conn.execute("SELECT MAX(last_seen) FROM items").fetchone()[0]
    stats['last_update'] = last

    queries = conn.execute(
        "SELECT query, COUNT(*) as count FROM items GROUP BY query ORDER BY count DESC"
    ).fetchall()
    stats['queries'] = [{"query": r['query'], "count": r['count']} for r in queries]

    conn.close()
    return stats
