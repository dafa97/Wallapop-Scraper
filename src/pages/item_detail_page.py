from selenium.webdriver.common.by import By

from src.pages.base_page import BasePage
from src.utils import extract_text_safe


class ItemDetailPage(BasePage):
    """Page Object para la página de detalle de un producto.

    Responsabilidades: navegar al detalle y extraer/completar
    título, precio, descripción y ubicación.
    """

    # ── Patrones de clase para campos del detalle ───────────
    TITLE_PATTERN = ["h1", "h2", "title"]
    PRICE_PATTERN = ["item-detail-price", "price"]
    DESCRIPTION_PATTERN = ["description", "item-detail-description"]
    LOCATION_PATTERN = ["item-detail-location", "location"]

    # Espera a que cargue el detalle (cualquier h1 en la página)
    PAGE_LOADED_INDICATOR = (By.TAG_NAME, "h1")

    def enrich_item(self, item):
        """Navega al detalle del item y completa los datos faltantes.

        Args:
            item: Dict con keys url, title, price, location, description.

        Returns:
            El mismo dict con los campos completados.
        """
        try:
            self.driver.get(item['url'])
            self.wait_for_element(self.PAGE_LOADED_INDICATOR)

            soup = self.get_soup()

            if item['title'] in ["No disponible", "pending"]:
                item['title'] = self._extract_title(soup)

            if item['price'] in ["No disponible", "pending"]:
                item['price'] = self.extract_from_pattern(soup, self.PRICE_PATTERN)

            if item['location'] in ["No disponible", "pending"]:
                item['location'] = self.extract_from_pattern(soup, self.LOCATION_PATTERN)

            item['description'] = self._extract_description(soup)

            self.logger.info(f"[Scraped] {item['title'][:30]}... | {item['price']}")
            return item

        except Exception as e:
            self.logger.error(f"Error en detalle {item['url']}: {e}")
            return item

    def _extract_title(self, soup):
        """Extrae el título con fallback a <h1> directo."""
        elem = self.find_by_class_pattern(soup, self.TITLE_PATTERN)
        if not elem:
            elem = soup.find('h1')
        return extract_text_safe(elem)

    def _extract_description(self, soup):
        """Extrae la descripción con fallback genérico."""
        elem = self.find_by_class_pattern(soup, self.DESCRIPTION_PATTERN)
        if not elem:
            elem = soup.find(
                lambda t: t.name in ['div', 'section']
                and 'class' in t.attrs
                and 'description' in str(t['class']).lower()
            )
        return extract_text_safe(elem)
