import time
import logging
import random

from src.config import Config
from src.driver import init_driver
from src.utils import setup_logging, save_to_csv
from src.pages import HomePage, SearchResultsPage, ItemDetailPage


class WallapopScraper:
    def __init__(self):
        self.driver = None
        self.config = Config
        self.timestamp = None

    def initialize(self, query):
        """Configuración inicial: logging y driver."""
        self.timestamp = setup_logging(query, self.config.LOG_DIR)
        logging.info("Inicializando driver...")
        self.driver = init_driver(headless=False, pos="izquierda")

    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def anti_detection_delay(self):
        """Pausa aleatoria entre requests como medida anti-detección."""
        delay = random.uniform(2.5, 5.0)
        logging.info(f"Anti-detección: esperando {delay:.1f}s...")
        time.sleep(delay)

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
            items = results.extract_items()

            if max_items:
                items = items[:max_items]

            logging.info(f"Procesando detalles para {len(items)} items...")

            # ── Detalle: enriquecer cada item ───────────────
            detail = ItemDetailPage(self.driver, timeout)
            full_items = []
            for i, item in enumerate(items):
                full_items.append(detail.enrich_item(item))
                if i < len(items) - 1:
                    self.anti_detection_delay()

            # ── Guardar CSV ─────────────────────────────────
            filename = f"wallapop_{query.replace(' ', '_')}_detalles_{self.timestamp}.csv"
            save_to_csv(full_items, filename, self.config.OUTPUT_DIR)

            logging.info("Proceso finalizado con éxito.")

        except Exception as e:
            logging.error(f"Error fatal en run: {e}")
        finally:
            self.cleanup()
