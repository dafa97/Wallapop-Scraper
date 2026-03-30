"""
Almacén compartido de eventos de scraping en tiempo real.

Tanto el scheduler como los scrapes forzados vía API escriben aquí.
El endpoint SSE lee desde aquí para hacer streaming al frontend.
"""

import threading

_lock = threading.Lock()

# query -> lista de eventos
_scrape_events: dict[str, list] = {}

# query -> True si el scrape sigue en curso
_active_scrapes: dict[str, bool] = {}


def start_scrape(query: str):
    """Registra el inicio de un scrape."""
    with _lock:
        _scrape_events[query] = []
        _active_scrapes[query] = True


def emit(query: str, event: dict):
    """Añade un evento al log de la query."""
    with _lock:
        if query in _scrape_events:
            _scrape_events[query].append(event)


def finish_scrape(query: str, event: dict | None = None):
    """Marca el scrape como terminado, opcionalmente con un evento final."""
    with _lock:
        _active_scrapes[query] = False
        if query in _scrape_events:
            last = _scrape_events[query][-1] if _scrape_events[query] else None
            if not last or last.get('type') not in ('done', 'error'):
                _scrape_events[query].append(event or {'type': 'done', 'saved': 0})


def get_events(query: str) -> list | None:
    with _lock:
        return list(_scrape_events[query]) if query in _scrape_events else None


def get_events_from(query: str, idx: int) -> list:
    with _lock:
        events = _scrape_events.get(query, [])
        return list(events[idx:])


def is_done(query: str) -> bool:
    with _lock:
        events = _scrape_events.get(query, [])
        return bool(events and events[-1].get('type') in ('done', 'error'))


def active_scrapes() -> list[str]:
    """Queries con scrape en curso en este momento."""
    with _lock:
        return [q for q, running in _active_scrapes.items() if running]


def recent_scrapes() -> list[dict]:
    """Todas las queries con eventos (activas + recientes), con estado."""
    with _lock:
        result = []
        for query, events in _scrape_events.items():
            done = bool(events and events[-1].get('type') in ('done', 'error'))
            result.append({
                'query': query,
                'active': _active_scrapes.get(query, False),
                'done': done,
                'events': len(events),
            })
        return result


def make_callback(query: str):
    """Devuelve un callable on_progress para pasar al WallapopScraper."""
    def callback(event: dict):
        emit(query, event)
    return callback
