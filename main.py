import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from iniciar_uc import iniciar_uc
import time
import logging
import os
from datetime import datetime

def setup_driver():
    logging.info("Initializing the driver.")
    driver = iniciar_uc(headless=False, pos="izquierda")
    return driver

def accept_cookies(driver):
    try:
        logging.info("Accepting cookies.")
        accept_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        accept_button.click()
        time.sleep(2)
    except Exception as e:
        logging.error(f"Error accepting cookies: {e}")

def perform_search(driver, query):
    try:
        logging.info(f"Searching for: {query}")
        search_box = driver.find_element(By.ID, "searchbox-form-input")
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)
    except Exception as e:
        logging.error(f"Error performing search: {e}")
        raise

def extract_item_data(item):
    data = {}
    data['url'] = item.get_attribute('href')
    try:
        data['Título'] = item.find_element(By.CSS_SELECTOR, "[class*='item-card_ItemCard__title__']").text
    except Exception as e:
        logging.warning(f"Error extracting title: {e}")
        data['Título'] = "No disponible"
    try:
        data['Precio'] = item.find_element(By.CSS_SELECTOR, "[class*='item-card_ItemCard__price__']").text
    except Exception as e:
        logging.warning(f"Error extracting price: {e}")
        data['Precio'] = "No disponible"
    data['Descripción'] = "No disponible"
    data['Ubicación'] = "No disponible"
    return data

def scrape_items(driver):
    logging.info("Starting data extraction from items.")
    data = []
    try:
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[class*='item-card_ItemCard--vertical__']")))
        items = driver.find_elements(By.CSS_SELECTOR, "a[class*='item-card_ItemCard--vertical__']")
        logging.info(f"Found {len(items)} items on the page.")
        for idx, item in enumerate(items):
            try:
                logging.info(f"Extracting data for item {idx + 1}")
                logging.debug(f"Item HTML preview: {item.get_attribute('outerHTML')[:200]}")
                item_data = extract_item_data(item)
                data.append(item_data)
                logging.info(f"Data extracted: {item_data}")
            except Exception as e:
                logging.error(f"Error extracting data for item {idx + 1}: {e}")
                continue
    except Exception as e:
        logging.error(f"Error finding items: {e}")
    return data

def scrape_detailed_data(driver, items):
    logging.info("Starting detailed data extraction.")
    for idx, item in enumerate(items):
        try:
            logging.info(f"Scraping details for item {idx + 1}: {item['Título']}")
            driver.get(item['url'])
            time.sleep(5)  # Wait for page to load
            # Extract description
            try:
                wait = WebDriverWait(driver, 10)
                desc_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section[class*='item-detail_ItemDetailTwoColumns__description__']")))
                item['Descripción'] = desc_element.text.strip()
                logging.info("Description extracted.")
            except Exception as e:
                item['Descripción'] = "No disponible"
                logging.warning(f"No description found for {item['url']}: {e}")
            # Extract location
            try:
                wait = WebDriverWait(driver, 10)
                loc_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[class*='item-detail-location_ItemDetailLocation__link']")))
                item['Ubicación'] = loc_element.text.strip()
                logging.info("Location extracted.")
            except Exception as e:
                item['Ubicación'] = "No disponible"
                logging.warning(f"No location found for {item['url']}: {e}")
        except Exception as e:
            logging.error(f"Error scraping {item['url']}: {e}")
            continue
    return items

def save_to_csv(data, filename):
    try:
        logging.info(f"Saving data to CSV: {filename}")
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["URL", "Título", "Precio", "Descripción", "Ubicación"])
            for item in data:
                writer.writerow([item['url'], item['Título'], item['Precio'], item['Descripción'], item['Ubicación']])
        logging.info("Data saved successfully.")
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")

    
def search_and_scrape(query):
    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/wallapop_{query.replace(' ', '_')}_{timestamp}.log"
    logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    driver = None
    try:
        driver = setup_driver()
        driver.get("https://www.wallapop.com/")
        time.sleep(5)
        accept_cookies(driver)
        perform_search(driver, query)
        data = scrape_items(driver)
        detailed_data = scrape_detailed_data(driver, data)
        csv_filename = f"output/wallapop_{'_'.join(query.split())}_details_{timestamp}.csv"
        save_to_csv(detailed_data, csv_filename)
    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                logging.info("Driver closed.")
            except OSError as e:
                logging.error(f"Error closing driver: {e}")

def main():
    # Hacer un menu simple para elegir la búsqueda
    query = input("Enter the search term (e.g., 'MacBook M2'): ")
    search_and_scrape(query)
    
if __name__ == "__main__":
    main()
