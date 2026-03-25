import logging
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.utils import extract_text_safe


class BasePage:
    """Clase base para todos los Page Objects.

    Encapsula las operaciones comunes: esperas explícitas,
    búsqueda por patrón de clase CSS, y parseo con BeautifulSoup.
    """

    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    # ── Esperas explícitas ──────────────────────────────────

    def wait_for_element(self, locator):
        """Espera a que un elemento esté presente en el DOM."""
        return WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located(locator)
        )

    def wait_for_clickable(self, locator):
        """Espera a que un elemento sea clickeable."""
        return WebDriverWait(self.driver, self.timeout).until(
            EC.element_to_be_clickable(locator)
        )

    def wait_for_all_elements(self, locator):
        """Espera a que todos los elementos matching estén presentes."""
        return WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_all_elements_located(locator)
        )

    # ── BeautifulSoup ───────────────────────────────────────

    def get_soup(self):
        """Parsea el page_source actual con BeautifulSoup."""
        return BeautifulSoup(self.driver.page_source, 'html.parser')

    # ── Búsqueda por patrón de clase ────────────────────────

    def find_by_class_pattern(self, parent, pattern):
        """Busca un elemento cuyas clases contengan el patrón.

        Args:
            parent: Elemento BS4 donde buscar.
            pattern: String o lista de strings. Si es lista,
                     prueba cada patrón en orden y retorna el primero que encuentre.
        """
        if isinstance(pattern, list):
            for p in pattern:
                found = self.find_by_class_pattern(parent, p)
                if found:
                    return found
            return None

        return parent.find(
            lambda tag: tag.name and 'class' in tag.attrs
            and any(pattern in c for c in tag['class'])
        )

    def extract_from_pattern(self, parent, pattern, default="No disponible"):
        """Busca por patrón de clase y extrae el texto."""
        elem = self.find_by_class_pattern(parent, pattern)
        return extract_text_safe(elem, default)
