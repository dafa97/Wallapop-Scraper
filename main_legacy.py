"""
Wallapop Scraper - Versión mejorada con selectores estables
Basado en análisis del DOM de Vue.js de Wallapop
"""

import csv
import json
import time
import logging
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import re
from iniciar_uc import iniciar_uc


class WallapopScraper:
    def __init__(self):
        self.driver = None
        self.wait_timeout = 15
        self.page_load_wait = 5
    
    def _extract_text_safe(self, element, default="No disponible"):
        """Extraer texto de forma segura con valor por defecto"""
        if element:
            text = element.get_text(strip=True)
            return text if text else default
        return default
    
    def _find_element_with_class_pattern(self, parent, pattern):
        """Buscar elemento cuyas clases contengan el patrón especificado"""
        return parent.find(lambda tag: tag.name and 'class' in tag.attrs 
                          and any(pattern in c for c in tag['class']))
    
    def _extract_location_from_card(self, card_element):
        """Intentar extraer ubicación desde una tarjeta de producto"""
        # Buscar elementos comunes de ubicación en las cards
        location_patterns = [
            lambda: card_element.find(lambda tag: tag.name and 'class' in tag.attrs 
                                     and any('location' in c.lower() for c in tag['class'])),
            lambda: card_element.find('span', class_=re.compile(r'ItemCard.*location', re.I)),
            lambda: card_element.find(lambda tag: tag.name == 'span' and 'class' in tag.attrs
                                     and any('distance' in c.lower() for c in tag['class']))
        ]
        
        for pattern_func in location_patterns:
            try:
                elem = pattern_func()
                if elem:
                    return self._extract_text_safe(elem, None)
            except:
                continue
        return None
        
    def setup_logging(self, query):
        """Configurar logging con timestamp"""
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/wallapop_{query.replace(' ', '_')}_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        return timestamp

    def setup_driver(self):
        """Inicializar Selenium con undetected-chrome"""
        logging.info("Inicializando driver...")
        self.driver = iniciar_uc(headless=False, pos="izquierda")
        return self.driver

    def accept_cookies(self):
        """Aceptar cookies de Wallapop"""
        try:
            logging.info("Aceptando cookies...")
            cookie_selectors = [
                "#onetrust-accept-btn-handler",
                "[id*='accept']",
                "button[class*='accept']",
                "[class*='btn_yes']",
            ]
            
            for selector in cookie_selectors:
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
        except Exception as e:
            logging.warning(f"Error aceptando cookies: {e}")
            return False

    def perform_search(self, query):
        """Realizar búsqueda en Wallapop"""
        try:
            logging.info(f"Buscando: {query}")
            search_box = self.driver.find_element(By.ID, "searchbox-form-input")
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            time.sleep(self.page_load_wait)
            logging.info("[OK] Búsqueda completada")
            return True
        except Exception as e:
            logging.error(f"[X] Error en búsqueda: {e}")
            return False

    def extract_items_from_listing(self):
        """Extraer datos básicos (URL, título, precio, ubicación) del listado usando BeautifulSoup"""
        logging.info("Extrayendo items del listado (BS4)...")
        items_data = []
        
        try:
            # Esperar a que cargue algo
            wait = WebDriverWait(self.driver, self.wait_timeout)
            wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a[class*='item-card_ItemCard']")
            ))
            time.sleep(2) # Espera extra para renderizado
            
            # Obtener HTML y parsear
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Regex para encontrar cards
            card_class_re = re.compile(r'item-card_ItemCard')
            cards = soup.find_all('a', class_=card_class_re)
            
            logging.info(f"[OK] Encontrados {len(cards)} items")
            
            for idx, card in enumerate(cards, 1):
                try:
                    # URL del producto
                    url = card.get('href')
                    if not url:
                        logging.debug(f"Card {idx}: No URL encontrada, omitiendo")
                        continue
                    
                    # Asegurar URL completa
                    if url.startswith('/'):
                        url = f"https://es.wallapop.com{url}"
                    elif not url.startswith('http'):
                        url = f"https://es.wallapop.com/{url}"
                    
                    # Título - Buscar con patrón de clase
                    title_elem = self._find_element_with_class_pattern(card, 'ItemCard__title')
                    title = self._extract_text_safe(title_elem, "No disponible")
                    
                    # Precio - Buscar con patrón de clase
                    price_elem = self._find_element_with_class_pattern(card, 'ItemCard__price')
                    price = self._extract_text_safe(price_elem, "No disponible")
                    
                    # Ubicación - Intentar extraer del listado
                    location = self._extract_location_from_card(card)
                    if not location:
                        location = 'pending'  # Se intentará en la página de detalle
                    
                    items_data.append({
                        'url': url,
                        'title': title,
                        'price': price,
                        'description': 'pending',
                        'location': location
                    })
                    
                    if title != "No disponible":
                        logging.debug(f"Card {idx}: {title[:30]}... - {price} - {location}")
                    else:
                        logging.debug(f"Card {idx}: URL={url[:50]}... - {price}")

                except Exception as e:
                    logging.warning(f"Error extrayendo card {idx}: {e}")
                    continue
            
            logging.info(f"[OK] {len(items_data)} items extraídos del listado")
            return items_data
            
        except Exception as e:
            logging.error(f"[X] Error extrayendo items del listado: {e}")
            return items_data

    def scrape_detail_page(self, item_data):
        """Raspar detalles de una página de producto usando BeautifulSoup"""
        url = item_data['url']
        
        try:
            logging.debug(f"Visitando: {url[:60]}...")
            self.driver.get(url)
            time.sleep(self.page_load_wait)
            
            # Obtener HTML y parsear con BeautifulSoup
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # TÍTULO - Solo si no se obtuvo o es "No disponible"
            if item_data.get('title') in ['pending', 'No disponible', None, '']:
                # Intentar varios selectores
                title_elem = (
                    soup.find('h1') or 
                    soup.find(lambda tag: tag.name and 'class' in tag.attrs 
                             and any('title' in c.lower() for c in tag['class'])) or
                    soup.find('h2')
                )
                if title_elem:
                    item_data['title'] = self._extract_text_safe(title_elem, "No disponible")
            
            # PRECIO - Solo si no se obtuvo o es "No disponible"
            if item_data.get('price') in ['pending', 'No disponible', None, '']:
                # Buscar precio con varios selectores
                price_elem = (
                    soup.find(lambda tag: tag.name and 'class' in tag.attrs 
                             and any('item-detail-price' in c.lower() for c in tag['class'])) or
                    soup.find(lambda tag: tag.name == 'span' and 'class' in tag.attrs
                             and any('price' in c.lower() for c in tag['class']))
                )
                if price_elem:
                    item_data['price'] = self._extract_text_safe(price_elem, "No disponible")
            
            # DESCRIPCIÓN
            if item_data.get('description') == 'pending':
                # Buscar sección de descripción
                desc_selectors = [
                    lambda: soup.find('section', class_=re.compile(r'item-detail.*description', re.I)),
                    lambda: soup.find('div', class_=re.compile(r'description', re.I)),
                    lambda: soup.find(lambda tag: tag.name in ['section', 'div'] and 'class' in tag.attrs
                                     and any('description' in c.lower() for c in tag['class']))
                ]
                
                desc_elem = None
                for selector_func in desc_selectors:
                    try:
                        desc_elem = selector_func()
                        if desc_elem:
                            break
                    except:
                        continue
                
                if desc_elem:
                    # Extraer solo el texto de la descripción, evitando etiquetas internas
                    desc_text = desc_elem.get_text(separator='\n', strip=True)
                    item_data['description'] = desc_text if desc_text else "No disponible"
                else:
                    item_data['description'] = "No disponible"
            
            # UBICACIÓN - Solo si no se obtuvo del listado
            if item_data.get('location') in ['pending', None, '']:
                # Buscar ubicación con varios selectores
                location_selectors = [
                    lambda: soup.find('a', class_=re.compile(r'item-detail-location.*link', re.I)),
                    lambda: soup.find(lambda tag: tag.name and 'class' in tag.attrs
                                     and any('location' in c.lower() for c in tag['class'])),
                    lambda: soup.find('span', class_=re.compile(r'location', re.I))
                ]
                
                location_elem = None
                for selector_func in location_selectors:
                    try:
                        location_elem = selector_func()
                        if location_elem:
                            break
                    except:
                        continue
                
                if location_elem:
                    item_data['location'] = self._extract_text_safe(location_elem, "No disponible")
                else:
                    item_data['location'] = "No disponible"
            
            # Log del resultado
            title_preview = item_data['title'][:40] if len(item_data['title']) > 40 else item_data['title']
            logging.info(f"[OK] {title_preview} - {item_data['price']} - {item_data['location']}")
            return item_data
            
        except Exception as e:
            logging.error(f"[X] Error scrapeando {url[:50]}: {e}")
            # Asegurar que no queden campos 'pending'
            if item_data.get('description') == 'pending':
                item_data['description'] = "No disponible"
            if item_data.get('location') == 'pending':
                item_data['location'] = "No disponible"
            return item_data

    def scrape_all_details(self, items):
        """Raspar detalles de todos los items"""
        logging.info(f"\nScrapeando {len(items)} items...")
        
        for idx, item in enumerate(items, 1):
            self.scrape_detail_page(item)
            if idx < len(items):
                time.sleep(2)
        
        return items

    def save_to_csv(self, data, filename):
        """Guardar datos en CSV"""
        try:
            logging.info(f"Guardando: {filename}")
            os.makedirs("output", exist_ok=True)
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['url', 'title', 'price', 'description', 'location'])
                writer.writeheader()
                writer.writerows(data)
            
            logging.info(f"[OK] {len(data)} items guardados")
            return True
        except Exception as e:
            logging.error(f"[X] Error guardando: {e}")
            return False

    def run(self, query, max_items=None):
        """Ejecutar el scraper completo"""
        timestamp = self.setup_logging(query)
        
        logging.info("\n" + "="*60)
        logging.info("WALLAPOP SCRAPER - MEJORADO")
        logging.info("="*60)
        
        try:
            self.setup_driver()
            logging.info("Navegando a Wallapop...")
            self.driver.get("https://www.wallapop.com/")
            time.sleep(3)
            
            self.accept_cookies()
            
            if not self.perform_search(query):
                return False
            
            items = self.extract_items_from_listing()
            if not items:
                return False
            
            if max_items:
                items = items[:max_items]
            
            items = self.scrape_all_details(items)
            
            filename = f"output/wallapop_{query.replace(' ', '_')}_detalles_{timestamp}.csv"
            self.save_to_csv(items, filename)
            
            logging.info("\n[OK] COMPLETADO")
            return True
            
        except Exception as e:
            logging.error(f"Error: {e}")
            return False
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

import sys

def main():
    print("Iniciando Wallapop Scraper...")
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Modo automático: Buscando '{query}'")
    else:
        query = input("Términode búsqueda (ej: 'MacBook'): ").strip()
    
    if not query:
        print("Búsqueda vacía.")
        return
    
    scraper = WallapopScraper()
    scraper.run(query)


if __name__ == "__main__":
    main()