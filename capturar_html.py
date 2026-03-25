"""
Script para capturar el HTML completo de Wallapop en 3 puntos:
  1. Página de inicio
  2. Resultados de búsqueda
  3. Detalle de un item

Guarda los HTML en html_capturas/ para análisis posterior de selectores.
"""

import sys
import os
import time
from datetime import datetime

from src.driver import init_driver
from src.config import Config
from src.pages import HomePage, SearchResultsPage


def guardar_html(html, nombre, carpeta):
    """Guarda el HTML en un archivo dentro de la carpeta indicada."""
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [OK] Guardado: {ruta} ({len(html):,} caracteres)")


def capturar(query):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta = os.path.join("html_capturas", f"{query.replace(' ', '_')}_{timestamp}")

    driver = None
    try:
        print("Inicializando driver...")
        driver = init_driver(headless=False, pos="izquierda")
        timeout = Config.TIMEOUT_DEFAULT

        # --- 1. Página de inicio ---
        print("\n[1/3] Capturando página de inicio...")
        driver.get(Config.BASE_URL)

        home = HomePage(driver, timeout)
        home.accept_cookies()

        guardar_html(driver.page_source, "01_inicio.html", carpeta)

        # --- 2. Resultados de búsqueda ---
        print(f"\n[2/3] Buscando '{query}' y capturando resultados...")
        home.search(query)
        time.sleep(3)

        # Scroll para cargar más items
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        guardar_html(driver.page_source, "02_busqueda.html", carpeta)

        # --- 3. Detalle del primer item ---
        print("\n[3/3] Entrando al detalle del primer item...")
        try:
            results = SearchResultsPage(driver, timeout)
            items = results.extract_items()

            if items:
                url_detalle = items[0]['url']
                driver.get(url_detalle)
                time.sleep(3)
                guardar_html(driver.page_source, "03_detalle.html", carpeta)
            else:
                print("  [!] No se encontraron items para capturar detalle")
        except Exception as e:
            print(f"  [!] No se pudo capturar detalle: {e}")

        print(f"\nCaptura completa. Archivos en: {carpeta}/")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Término de búsqueda (ej: 'MacBook'): ").strip()

    if not query:
        print("Búsqueda vacía. Saliendo.")
    else:
        capturar(query)
