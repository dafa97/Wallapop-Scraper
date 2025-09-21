# Wallapop Scraper

A Python script to scrape item listings from Wallapop.com using Selenium and undetected-chromedriver.

## Features

- Searches for items on Wallapop based on a query
- Extracts item URLs, titles, prices, descriptions, and locations
- Saves results to CSV files with timestamps
- Logs each search run separately with timestamps
- Uses undetected Chrome driver to avoid detection

## Installation

1. Clone or download this repository.

2. Install Python 3.x if not already installed.

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Ensure you have chromedriver in the project directory. For Windows, use `chromedriver.exe` and `chromedriver-win64/` folder.

## Usage

Run the script with:
```
python main.py
```

Enter your search query when prompted, e.g., "MacBook M2".

The script will:
- Open a browser window (positioned to the left for better monitoring)
- Search on Wallapop
- Scrape item data and details
- Save CSV output to `output/` folder with timestamp (e.g., `wallapop_MacBook_M2_details_20230921_165803.csv`)
- Save logs to `logs/` folder with timestamp (e.g., `wallapop_MacBook_M2_20230921_165803.log`)

## CSV Output Format

The CSV file contains columns:
- URL: The item's Wallapop URL
- Título: Item title
- Precio: Price
- Descripción: Description
- Ubicación: Location

## Logs

Each search generates a separate log file in the `logs/` directory, including INFO and WARNING messages from the scraping process.

## Requirements

- Python 3.x
- Google Chrome browser
- Internet connection

## Notes

- The script uses undetected-chromedriver to bypass anti-bot measures.
- Browser window is set to non-headless by default for monitoring.
- Directories `output/` and `logs/` are created automatically if they don't exist.
