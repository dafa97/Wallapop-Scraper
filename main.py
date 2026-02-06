
import sys
from src.scraper import WallapopScraper

def main():
    print("Iniciando Wallapop Scraper (Estructura Modular)...")
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Modo automático: Buscando '{query}'")
    else:
        query = input("Término de búsqueda (ej: 'MacBook'): ").strip()
    
    if not query:
        print("Búsqueda vacía. Saliendo.")
        return
    
    scraper = WallapopScraper()
    # Puedes pasar max_items=5 para pruebas rápidas
    scraper.run(query)

if __name__ == "__main__":
    main()
