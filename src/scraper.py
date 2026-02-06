import time
import logging
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.config import Config
from src.driver import init_driver
from src.utils import setup_logging, save_to_csv, extract_text_safe

class WallapopScraper:
    def __init__(self):
        self.driver = None
        self.config = Config
        self.timestamp = None

    def _find_element_with_class_pattern(self, parent, pattern):
        """Buscar elemento cuyas clases contengan el patrón especificado"""
        # Si pattern es una lista, busca cualquiera de ellos
        if isinstance(pattern, list):
            for p in pattern:
                found = self._find_element_with_class_pattern(parent, p)
                if found: return found
            return None
            
        return parent.find(lambda tag: tag.name and 'class' in tag.attrs 
                          and any(pattern in c for c in tag['class']))

    def initialize(self, query):
        """Configuración inicial"""
        self.timestamp = setup_logging(query, self.config.LOG_DIR)
        logging.info("Inicializando driver...")
        self.driver = init_driver(headless=False, pos="izquierda")

    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def accept_cookies(self):
        """Aceptar cookies usando los selectores de config"""
        logging.info("Aceptando cookies...")
        for selector in self.config.SELECTORS["cookies"]:
            try:
                accept_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                accept_button.click()
                logging.info(f"[OK] Cookies aceptadas")
                time.sleep(1)
                return True
            except Exception:
                continue
        logging.warning("[!] No se encontró botón de cookies")
        return False

    def search(self, query):
        """Realizar búsqueda"""
        try:
            logging.info(f"Buscando: {query}")
            search_box_id = self.config.SELECTORS["search_box"]["id"]
            search_box = self.driver.find_element(By.ID, search_box_id)
            
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            time.sleep(self.config.PAGE_LOAD_WAIT)
            return True
        except Exception as e:
            logging.error(f"[X] Error en búsqueda: {e}")
            return False

    def extract_list_items(self):
        """Extrae items de la lista de resultados"""
        logging.info("Extrayendo listado...")
        items_data = []
        
        try:
            # Esperar elementos
            wait = WebDriverWait(self.driver, self.config.TIMEOUT_DEFAULT)
            wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, self.config.SELECTORS["item_card"])
            ))
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # Usar regex para ser flexible con la clase del card
            card_class_re = re.compile(r'item-card_ItemCard')
            cards = soup.find_all('a', class_=card_class_re)
            
            logging.info(f"Encontrados {len(cards)} items en listado.")
            
            for idx, card in enumerate(cards, 1):
                try:
                    url = card.get('href')
                    if not url: continue
                    
                    if url.startswith('/'):
                        url = f"{self.config.BASE_URL.rstrip('/')}{url}"
                    
                    # Extraer datos básicos del card
                    title_elem = self._find_element_with_class_pattern(card, self.config.SELECTORS["card_patterns"]["title"])
                    price_elem = self._find_element_with_class_pattern(card, self.config.SELECTORS["card_patterns"]["price"])
                    
                    # Ubicación en card
                    loc_elem = self._find_element_with_class_pattern(card, self.config.SELECTORS["card_patterns"]["location"])

                    items_data.append({
                        'url': url,
                        'title': extract_text_safe(title_elem, "No disponible"),
                        'price': extract_text_safe(price_elem, "No disponible"),
                        'location': extract_text_safe(loc_elem, "pending"), # 'pending' para reintentar en detalle
                        'description': 'pending'
                    })
                except Exception as e:
                    logging.warning(f"Error parseando card {idx}: {e}")
                    
            return items_data
        except Exception as e:
            logging.error(f"Error general extrayendo lista: {e}")
            return []

    def scrape_detail(self, item):
        """Entra al detalle para obtener descripción y completar datos"""
        try:
            self.driver.get(item['url'])
            time.sleep(self.config.PAGE_LOAD_WAIT)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Completar Title
            if item['title'] in ["No disponible", "pending"]:
                elem = self._find_element_with_class_pattern(soup, self.config.SELECTORS["detail"]["title"])
                # Fallback a h1 directo si no encuentra por clase
                if not elem: elem = soup.find('h1')
                item['title'] = extract_text_safe(elem, "No disponible")

            # Completar Price
            if item['price'] in ["No disponible", "pending"]:
                elem = self._find_element_with_class_pattern(soup, self.config.SELECTORS["detail"]["price"])
                item['price'] = extract_text_safe(elem, "No disponible")

            # Completar Location
            if item['location'] in ["No disponible", "pending"]:
                elem = self._find_element_with_class_pattern(soup, self.config.SELECTORS["detail"]["location"])
                item['location'] = extract_text_safe(elem, "No disponible")

            # Obtener Descripción
            desc_elem = self._find_element_with_class_pattern(soup, self.config.SELECTORS["detail"]["description"])
            if not desc_elem:
                # Intento genérico por div/section con 'description' en clase
                desc_elem = soup.find(lambda t: t.name in ['div','section'] and 'class' in t.attrs and 'description' in str(t['class']).lower())
            
            item['description'] = extract_text_safe(desc_elem, "No disponible")
            
            logging.info(f"[Scraped] {item['title'][:30]}... | {item['price']}")
            return item

        except Exception as e:
            logging.error(f"Error en detalle {item['url']}: {e}")
            return item

    def run(self, query, max_items=None):
        try:
            self.initialize(query)
            
            # Si no se especifica por argumento, usar el de configuración
            if max_items is None:
                max_items = getattr(self.config, 'MAX_ITEMS', None)

            logging.info("="*50)
            logging.info(f"SCRAPER WALLAPOP: {query}")
            logging.info("="*50)

            self.driver.get(self.config.BASE_URL)
            time.sleep(2)
            self.accept_cookies()
            
            if not self.search(query):
                return
            
            items = self.extract_list_items()
            
            if max_items:
                items = items[:max_items]
                
            logging.info(f"Procesando detalles para {len(items)} items...")
            
            full_items = []
            for i, item in enumerate(items):
                full_items.append(self.scrape_detail(item))
                if i < len(items) - 1:
                    time.sleep(2) # Pausa cortés
            
            # Guardar
            filename = f"wallapop_{query.replace(' ', '_')}_detalles_{self.timestamp}.csv"
            save_to_csv(full_items, filename, self.config.OUTPUT_DIR)
            
            logging.info("Proceso finalizado con éxito.")
            
        except Exception as e:
            logging.error(f"Error fatal en run: {e}")
        finally:
            self.cleanup()
