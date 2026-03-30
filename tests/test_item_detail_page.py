import pytest
from unittest.mock import MagicMock
from bs4 import BeautifulSoup
from src.pages.item_detail_page import ItemDetailPage


def make_page(mock_driver, html=""):
    mock_driver.page_source = html
    page = ItemDetailPage(mock_driver, timeout=1)
    page.wait_for_element = MagicMock(return_value=MagicMock())
    return page


def parse(html):
    return BeautifulSoup(html, "html.parser")


# ── _extract_title ───────────────────────────────────────────────────────────

def test_extract_title_via_clase(mock_driver, item_detail_html):
    page = make_page(mock_driver)
    soup = parse(item_detail_html)
    title = page._extract_title(soup)
    assert title == "MacBook Pro M1 16GB 512GB Space Gray"


def test_extract_title_fallback_a_h1(mock_driver):
    page = make_page(mock_driver)
    soup = parse("<div><h1>Título de prueba</h1></div>")
    title = page._extract_title(soup)
    assert title == "Título de prueba"


def test_extract_title_sin_h1_devuelve_no_disponible(mock_driver):
    page = make_page(mock_driver)
    soup = parse("<div>Sin título</div>")
    title = page._extract_title(soup)
    assert title == "No disponible"


# ── _extract_description ─────────────────────────────────────────────────────

def test_extract_description_via_clase(mock_driver, item_detail_html):
    page = make_page(mock_driver)
    soup = parse(item_detail_html)
    desc = page._extract_description(soup)
    assert "perfecto estado" in desc


def test_extract_description_fallback_generico(mock_driver):
    page = make_page(mock_driver)
    # Clase con "description" en nombre pero no el patrón exacto
    html = '<div class="my-description-wrapper">Texto del fallback</div>'
    soup = parse(html)
    desc = page._extract_description(soup)
    assert desc == "Texto del fallback"


def test_extract_description_sin_descripcion_devuelve_no_disponible(mock_driver):
    page = make_page(mock_driver)
    soup = parse("<div>Sin descripción</div>")
    desc = page._extract_description(soup)
    assert desc == "No disponible"


# ── enrich_item ──────────────────────────────────────────────────────────────

def _make_item(**kwargs):
    base = {
        "url": "https://www.wallapop.com/item/test123",
        "title": "pending",
        "price": "pending",
        "location": "pending",
        "description": "pending",
    }
    base.update(kwargs)
    return base


def test_enrich_rellena_title_pending(mock_driver, item_detail_html):
    page = make_page(mock_driver, item_detail_html)
    item = _make_item(title="pending")
    result = page.enrich_item(item)
    assert result["title"] != "pending"
    assert result["title"] != "No disponible"


def test_enrich_rellena_price_pending(mock_driver, item_detail_html):
    page = make_page(mock_driver, item_detail_html)
    item = _make_item(price="pending")
    result = page.enrich_item(item)
    assert result["price"] == "800€"


def test_enrich_siempre_rellena_description(mock_driver, item_detail_html):
    page = make_page(mock_driver, item_detail_html)
    item = _make_item(description="pending")
    result = page.enrich_item(item)
    assert result["description"] != "pending"
    assert "perfecto estado" in result["description"]


def test_enrich_preserva_title_real(mock_driver, item_detail_html):
    page = make_page(mock_driver, item_detail_html)
    item = _make_item(title="Título ya conocido")
    result = page.enrich_item(item)
    # No es "pending" ni "No disponible", así que no se reemplaza
    assert result["title"] == "Título ya conocido"


def test_enrich_devuelve_item_en_excepcion(mock_driver):
    page = make_page(mock_driver)
    page.driver.get.side_effect = Exception("driver muerto")
    item = _make_item()
    result = page.enrich_item(item)
    # Debe devolver el item original sin explotar
    assert result["url"] == "https://www.wallapop.com/item/test123"


def test_enrich_rellena_location_pending(mock_driver, item_detail_html):
    page = make_page(mock_driver, item_detail_html)
    item = _make_item(location="pending")
    result = page.enrich_item(item)
    assert result["location"] == "Madrid, España"
