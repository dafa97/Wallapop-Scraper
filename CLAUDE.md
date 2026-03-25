# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wallapop Scraper is a Python Selenium-based web scraper that searches Wallapop.com for item listings, extracts details (title, price, description, location), and saves results to CSV. It uses `undetected-chromedriver` to bypass anti-bot detection.

## Commands

```bash
# Setup
pip install -r requirements.txt

# Run (interactive prompt for search query)
python main.py

# Run with query argument
python main.py MacBook M2
```

There are no tests or linters configured.

## Architecture

**Entry point:** `main.py` - accepts search query via CLI args or interactive prompt, instantiates `WallapopScraper` and calls `run()`.

**`src/` modules:**

- **`scraper.py`** (`WallapopScraper` class) - orchestrates the full scrape pipeline: initialize driver, navigate to Wallapop, accept cookies, search, extract list items via BeautifulSoup, visit each detail page, save CSV. The `run(query, max_items)` method is the main entry point.
- **`driver.py`** (`init_driver`) - initializes `undetected_chromedriver` with a pinned Chrome version (`version_main=144`). Includes cache cleanup retry logic and window positioning.
- **`config.py`** (`Config` class) - centralized constants: URLs, timeouts, CSS selectors for cookies/search/cards/detail pages, and `MAX_ITEMS` limit.
- **`utils.py`** - logging setup (per-query log files in `logs/`), CSV export to `output/`, and `extract_text_safe` helper for BeautifulSoup elements.

**Data flow:** Search results page -> BeautifulSoup parses item cards (CSS class pattern matching) -> visits each item detail URL -> enriches data from detail page -> writes CSV.

## Key Details

- **Language:** Spanish (variable names, logs, UI prompts, comments are all in Spanish)
- **CSS selectors are fragile:** Wallapop updates their HTML frequently. Selectors in `Config.SELECTORS` use partial class name matching (e.g., `item-card_ItemCard`) and will break when Wallapop changes their frontend. The `_find_element_with_class_pattern` method in `scraper.py` handles this flexible matching.
- **Chrome version pinned** to 144 in `driver.py` - must be updated when the local Chrome installation updates.
- **Intentional delays** (`time.sleep`) throughout the scraper are anti-detection measures; do not remove them.
- **Output directories** (`output/`, `logs/`) are auto-created and gitignored.
- **`chromedriver.exe`** must be present locally but is gitignored.
