import re
import time

from selenium.webdriver.common.by import By

from src.pages.base_page import BasePage
from src.utils import extract_text_safe


class SearchResultsPage(BasePage):
    """Page Object para la página de resultados de búsqueda.

    Responsabilidades: esperar a que carguen los resultados,
    hacer scroll para cargar todas las páginas, y extraer los
    datos básicos de cada card de producto.
    """

    BASE_URL = "https://www.wallapop.com"

    # ── Selectores propios de esta página ───────────────────
    ITEM_CARD = (By.CSS_SELECTOR, "a[class*='item-card_ItemCard']")
    CARD_CLASS_RE = re.compile(r'item-card_ItemCard')

    # Patrones de clase para campos dentro del card
    CARD_TITLE_PATTERN = "ItemCard__title"
    CARD_PRICE_PATTERN = "ItemCard__price"
    CARD_LOCATION_PATTERN = ["location", "distance"]

    # Configuración de scroll
    SCROLL_PAUSE = 5        # Segundos de espera tras cada scroll
    MAX_SCROLL_RETRIES = 3  # Scrolls consecutivos sin nuevos items antes de parar

    def _scroll_to_load_all(self, max_items=None):
        """Hace scroll hasta el final de la página para cargar todos los resultados.

        Wallapop usa scroll infinito: al llegar al fondo se cargan más items.
        Dejamos de hacer scroll cuando no aparecen items nuevos tras varios intentos,
        o cuando alcanzamos max_items.
        """
        prev_count = 0
        retries = 0

        while True:
            # Contar items actuales
            cards = self.driver.find_elements(*self.ITEM_CARD)
            current_count = len(cards)

            self.logger.info(f"Scroll: {current_count} items cargados...")

            # Si ya tenemos suficientes items, parar
            if max_items and current_count >= max_items:
                self.logger.info(f"Alcanzado máximo de {max_items} items.")
                break

            # Si cargaron nuevos items, resetear retries
            if current_count > prev_count:
                retries = 0
                prev_count = current_count
            else:
                retries += 1
                if retries >= self.MAX_SCROLL_RETRIES:
                    self.logger.info("No se encontraron más items tras varios scrolls. Fin de resultados.")
                    break

            # Scroll al fondo de la página
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.SCROLL_PAUSE)

    def extract_items(self, max_items=None):
        """Extrae la lista de items de los resultados, haciendo scroll para cargar todos.

        Args:
            max_items: Número máximo de items a extraer (None para todos).

        Returns:
            Lista de dicts con keys: url, title, price, location, description.
        """
        self.logger.info("Extrayendo listado...")
        items_data = []

        # Esperar a que al menos un card esté presente
        self.wait_for_all_elements(self.ITEM_CARD)

        # Scroll para cargar más resultados
        self._scroll_to_load_all(max_items)

        soup = self.get_soup()
        cards = soup.find_all('a', class_=self.CARD_CLASS_RE)
        self.logger.info(f"Encontrados {len(cards)} items en total.")

        for idx, card in enumerate(cards, 1):
            if max_items and len(items_data) >= max_items:
                break

            try:
                url = card.get('href')
                if not url:
                    continue

                if url.startswith('/'):
                    url = f"{self.BASE_URL}{url}"

                items_data.append({
                    'url': url,
                    'title': self.extract_from_pattern(card, self.CARD_TITLE_PATTERN),
                    'price': self.extract_from_pattern(card, self.CARD_PRICE_PATTERN),
                    'location': self.extract_from_pattern(card, self.CARD_LOCATION_PATTERN, default="pending"),
                    'description': 'pending'
                })
            except Exception as e:
                self.logger.warning(f"Error parseando card {idx}: {e}")

        return items_data
