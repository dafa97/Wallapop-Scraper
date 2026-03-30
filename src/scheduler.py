"""
Scheduler para ejecutar scrapes de Wallapop periódicamente.

Lee las búsquedas configuradas en searches.json y ejecuta cada una
según su intervalo definido, usando WallapopScraper en modo headless.
"""

import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta

from src.scraper import WallapopScraper
import src.events as ev

logger = logging.getLogger(__name__)

SEARCHES_FILE = Path(__file__).resolve().parent.parent / "searches.json"
CONFIG_RELOAD_INTERVAL = 300  # Recargar searches.json cada 5 minutos


def _load_searches(path=SEARCHES_FILE):
    """Carga y valida las búsquedas desde el archivo JSON."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        searches = data.get("searches", [])
        if not searches:
            logger.warning("No se encontraron búsquedas en %s", path)
        return searches
    except FileNotFoundError:
        logger.error("Archivo de búsquedas no encontrado: %s", path)
        return []
    except json.JSONDecodeError as e:
        logger.error("Error al parsear %s: %s", path, e)
        return []


def _run_single_search(query, max_items=None):
    """Ejecuta un scrape individual en modo headless."""
    ev.start_scrape(query)
    try:
        scraper = WallapopScraper(headless=True, on_progress=ev.make_callback(query))
        scraper.run(query, max_items=max_items)
    except Exception as e:
        logger.error("Error ejecutando scrape para '%s': %s", query, e)
        ev.finish_scrape(query, {'type': 'error', 'message': str(e)})
    finally:
        ev.finish_scrape(query)


class Scheduler:
    """Gestiona la ejecución periódica de búsquedas en Wallapop."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._searches = []
        self._next_run = {}  # query -> datetime de próxima ejecución
        self._last_config_load = None

    def stop(self):
        """Detiene el scheduler de forma limpia."""
        logger.info("Solicitando detención del scheduler...")
        self._stop_event.set()

    @property
    def running(self):
        return not self._stop_event.is_set()

    def _reload_config_if_needed(self):
        """Recarga searches.json periódicamente."""
        now = datetime.now()
        if (
            self._last_config_load is None
            or (now - self._last_config_load).total_seconds() >= CONFIG_RELOAD_INTERVAL
        ):
            new_searches = _load_searches()
            if new_searches:
                # Detectar búsquedas nuevas para programarlas inmediatamente
                existing_queries = {s["query"] for s in self._searches}
                for s in new_searches:
                    if s["query"] not in existing_queries:
                        self._next_run[s["query"]] = now
                        logger.info(
                            "Nueva búsqueda detectada: '%s' (cada %d min)",
                            s["query"],
                            s.get("interval_minutes", 60),
                        )
                self._searches = new_searches
            self._last_config_load = now

    def _process_searches(self):
        """Revisa y ejecuta las búsquedas que toca ejecutar."""
        now = datetime.now()
        for search in self._searches:
            if self._stop_event.is_set():
                break

            query = search["query"]
            interval = search.get("interval_minutes", 60)

            # Programar primera ejecución si no existe
            if query not in self._next_run:
                self._next_run[query] = now

            if now >= self._next_run[query]:
                logger.info("Iniciando scrape: '%s'", query)
                start = time.time()
                try:
                    _run_single_search(query)
                    elapsed = time.time() - start
                    logger.info(
                        "Scrape completado: '%s' (%.1fs)", query, elapsed
                    )
                except Exception as e:
                    logger.error(
                        "Error inesperado en scrape '%s': %s", query, e
                    )

                # Programar siguiente ejecución independientemente del resultado
                self._next_run[query] = datetime.now() + timedelta(
                    minutes=interval
                )
                logger.info(
                    "Próxima ejecución de '%s': %s",
                    query,
                    self._next_run[query].strftime("%H:%M:%S"),
                )

    def run(self):
        """Bucle principal del scheduler. Corre indefinidamente hasta que se llame stop()."""
        logger.info("Scheduler iniciado")

        while not self._stop_event.is_set():
            self._reload_config_if_needed()
            self._process_searches()

            # Esperar 10 segundos entre ciclos (permite detención rápida)
            self._stop_event.wait(timeout=10)

        logger.info("Scheduler detenido")


def run_scheduler():
    """Entry point principal. Ejecuta el scheduler indefinidamente."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    scheduler = Scheduler()

    # Permitir detención limpia con Ctrl+C
    try:
        scheduler.run()
    except KeyboardInterrupt:
        logger.info("Interrupción por teclado recibida")
        scheduler.stop()

    return scheduler


if __name__ == "__main__":
    run_scheduler()
