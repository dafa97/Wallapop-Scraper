import os
import csv
import logging
from datetime import datetime

def setup_logging(query, log_dir="logs"):
    """Configura el sistema de logging"""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"wallapop_{query.replace(' ', '_')}_{timestamp}.log")
    
    # Reset handlers si ya existen
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return timestamp

def save_to_csv(data, filename, output_dir="output"):
    """Guarda una lista de diccionarios en CSV"""
    if not data:
        logging.warning("No hay datos para guardar.")
        return False
        
    try:
        logging.info(f"Guardando fichero: {filename}")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        fieldnames = ['url', 'title', 'price', 'description', 'location']
        # Asegurar que todas las claves existen
        for item in data:
            for field in fieldnames:
                if field not in item:
                    item[field] = "No disponible"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        logging.info(f"[OK] {len(data)} items guardados en {filepath}")
        return True
    except Exception as e:
        logging.error(f"[X] Error guardando CSV: {e}")
        return False

def extract_text_safe(element, default="No disponible"):
    """Helper para extraer texto de BS4 elements"""
    if element:
        text = element.get_text(separator=' ', strip=True)
        return text if text else default
    return default
