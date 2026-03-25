import re

from selenium.webdriver.common.by import By

from src.pages.base_page import BasePage
from src.utils import extract_text_safe


class SearchResultsPage(BasePage):
    """Page Object para la página de resultados de búsqueda.

    Responsabilidades: esperar a que carguen los resultados y
    extraer los datos básicos de cada card de producto.
    """

    BASE_URL = "https://www.wallapop.com"

    # ── Selectores propios de esta página ───────────────────
    ITEM_CARD = (By.CSS_SELECTOR, "a[class*='item-card_ItemCard']")
    CARD_CLASS_RE = re.compile(r'item-card_ItemCard')

    # Patrones de clase para campos dentro del card
    CARD_TITLE_PATTERN = "ItemCard__title"
    CARD_PRICE_PATTERN = "ItemCard__price"
    CARD_LOCATION_PATTERN = ["location", "distance"]

    def extract_items(self):
        """Extrae la lista de items visibles en los resultados.

        Returns:
            Lista de dicts con keys: url, title, price, location, description.
        """
        self.logger.info("Extrayendo listado...")
        items_data = []

        # Esperar a que al menos un card esté presente
        self.wait_for_all_elements(self.ITEM_CARD)

        soup = self.get_soup()
        cards = soup.find_all('a', class_=self.CARD_CLASS_RE)
        self.logger.info(f"Encontrados {len(cards)} items en listado.")

        for idx, card in enumerate(cards, 1):
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
