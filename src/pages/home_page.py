from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from src.pages.base_page import BasePage


class HomePage(BasePage):
    """Page Object para la página principal de Wallapop.

    Responsabilidades: aceptar cookies y realizar búsquedas.
    """

    # ── Selectores propios de esta página ───────────────────
    SEARCH_BOX = (By.ID, "searchbox-form-input")

    # El banner de cookies de consentmanager.net se renderiza dentro
    # del Shadow DOM de #cmpwrapper, por lo que no es accesible con
    # selectores CSS normales de Selenium. Se usa JavaScript para
    # acceder al shadow root y hacer click en el botón "Aceptar todo".
    _JS_CLICK_ACCEPT_COOKIES = """
        var wrapper = document.getElementById('cmpwrapper');
        if (!wrapper || !wrapper.shadowRoot) return false;
        var btn = wrapper.shadowRoot.querySelector('.cmptxt_btn_yes');
        if (!btn) return false;
        btn.click();
        return true;
    """

    def accept_cookies(self):
        """Acepta el banner de cookies si aparece (Shadow DOM)."""
        self.logger.info("Aceptando cookies...")
        try:
            # Esperar a que el wrapper exista en el DOM
            self.wait_for_element((By.ID, "cmpwrapper"))
            # El shadow root se hidrata de forma asíncrona, reintentamos
            from selenium.webdriver.support.ui import WebDriverWait
            accepted = WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.execute_script(self._JS_CLICK_ACCEPT_COOKIES)
            )
            if accepted:
                self.logger.info("[OK] Cookies aceptadas")
                return True
        except Exception:
            pass
        self.logger.warning("[!] No se encontró botón de cookies")
        return False

    def search(self, query):
        """Escribe la query en el buscador y lanza la búsqueda."""
        self.logger.info(f"Buscando: {query}")
        search_box = self.wait_for_clickable(self.SEARCH_BOX)
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
