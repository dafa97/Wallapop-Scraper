
class Config:
    BASE_URL = "https://www.wallapop.com/"
    TIMEOUT_DEFAULT = 15
    PAGE_LOAD_WAIT = 5
    
    # Directorios
    LOG_DIR = "logs"
    OUTPUT_DIR = "output"
    
    # Límites
    MAX_ITEMS = 3 # Máximo número de elementos a scrapear (None para todos)

    # Selectors
    SELECTORS = {
        "cookies": [
            "#cmptxt_btn_yes"
        ],
        "search_box": {
            "id": "searchbox-form-input"
        },
        "item_card": "a[class*='item-card_ItemCard']",
        "card_patterns": {
            "title": "ItemCard__title",
            "price": "ItemCard__price",
            "location": ["location", "distance"]
        },
        "detail": {
            "title": ["h1", "h2", "title"],
            "price": ["item-detail-price", "price"],
            "description": ["description", "item-detail-description"],
            "location": ["item-detail-location", "location"]
        }
    }
