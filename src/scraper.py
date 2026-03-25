import time
import logging
import random

from src.config import Config
from src.driver import init_driver
from src.utils import setup_logging, save_to_csv
from src.database import save_items_to_db
from src.pages import HomePage, SearchResultsPage, ItemDetailPage


class WallapopScraper:
    BATCH_SIZE = 25  # Reiniciar driver cada N items para evitar memory leaks

    def __init__(self, headless=False):
        self.driver = None
        self.config = Config
        self.timestamp = None
        self.headless = headless

    def initialize(self, query):
        """Configuración inicial: logging y driver."""
        self.timestamp = setup_logging(query, self.config.LOG_DIR)
        logging.info("Inicializando driver...")
        self.driver = init_driver(headless=self.headless, pos="izquierda")

    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def _is_driver_alive(self):
        """Verifica si el driver/Chrome sigue respondiendo."""
        try:
            self.driver.execute_script("return 1")
            return True
        except Exception:
            return False

    def _restart_driver(self):
        """Reinicia el driver cuando Chrome se ha caído."""
        logging.warning("Driver no responde. Reiniciando Chrome...")
        self.cleanup()
        time.sleep(2)
        self.driver = init_driver(headless=self.headless, pos="izquierda")
        logging.info("Driver reiniciado correctamente.")

    def anti_detection_delay(self):
        """Pausa aleatoria entre requests como medida anti-detección."""
        delay = random.uniform(2.5, 5.0)
        logging.info(f"Anti-detección: esperando {delay:.1f}s...")
        time.sleep(delay)

    def _enrich_items_with_recovery(self, items, timeout):
        """Enriquece items con detalle, reiniciando el driver si se cae."""
        detail = ItemDetailPage(self.driver, timeout)
        full_items = []
        consecutive_failures = 0
        max_consecutive_failures = 3

        for i, item in enumerate(items):
            # Reiniciar driver cada BATCH_SIZE items para liberar memoria
            if i > 0 and i % self.BATCH_SIZE == 0:
                logging.info(f"Reiniciando driver (batch {i // self.BATCH_SIZE})...")
                self._restart_driver()
                detail = ItemDetailPage(self.driver, timeout)

            # Verificar que el driver sigue vivo antes de navegar
            if not self._is_driver_alive():
                self._restart_driver()
                detail = ItemDetailPage(self.driver, timeout)
                consecutive_failures = 0

            enriched = detail.enrich_item(item)
            full_items.append(enriched)

            # Detectar si el enrich falló (el item vuelve sin cambios)
            if enriched.get('description') in [None, 'No disponible', 'pending']:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    logging.warning(f"{consecutive_failures} fallos consecutivos. Reiniciando driver...")
                    self._restart_driver()
                    detail = ItemDetailPage(self.driver, timeout)
                    consecutive_failures = 0
            else:
                consecutive_failures = 0

            if i < len(items) - 1:
                self.anti_detection_delay()

        return full_items

    def run(self, query, max_items=None):
        try:
            self.initialize(query)

            if max_items is None:
                max_items = getattr(self.config, 'MAX_ITEMS', None)

            logging.info("=" * 50)
            logging.info(f"SCRAPER WALLAPOP: {query}")
            logging.info("=" * 50)

            timeout = self.config.TIMEOUT_DEFAULT

            # ── Home: cookies + búsqueda ────────────────────
            home = HomePage(self.driver, timeout)
            self.driver.get(self.config.BASE_URL)
            home.accept_cookies()
            home.search(query)

            # ── Resultados: extraer cards ───────────────────
            results = SearchResultsPage(self.driver, timeout)
            items = results.extract_items(max_items=max_items)

            logging.info(f"Procesando detalles para {len(items)} items...")

            # ── Detalle: enriquecer cada item con recuperación ─
            full_items = self._enrich_items_with_recovery(items, timeout)

            # ── Guardar en DB ─────────────────────────────────
            save_items_to_db(full_items, query)

            # ── Guardar CSV (backup) ──────────────────────────
            filename = f"wallapop_{query.replace(' ', '_')}_detalles_{self.timestamp}.csv"
            save_to_csv(full_items, filename, self.config.OUTPUT_DIR)

            logging.info("Proceso finalizado con éxito.")

        except Exception as e:
            logging.error(f"Error fatal en run: {e}")
        finally:
            self.cleanup()
