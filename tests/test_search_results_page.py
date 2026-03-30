import pytest
from unittest.mock import MagicMock, patch
from src.pages.search_results_page import SearchResultsPage


def make_page(mock_driver, html=""):
    mock_driver.page_source = html
    page = SearchResultsPage(mock_driver, timeout=1)
    # Evitar esperas reales de Selenium
    page.wait_for_all_elements = MagicMock(return_value=[])
    page._scroll_to_load_all = MagicMock()
    return page


# ── extract_items ────────────────────────────────────────────────────────────

def test_extract_items_devuelve_lista(mock_driver, search_results_html):
    page = make_page(mock_driver, search_results_html)
    items = page.extract_items()
    assert isinstance(items, list)
    assert len(items) == 5


def test_extract_items_campos_presentes(mock_driver, search_results_html):
    page = make_page(mock_driver, search_results_html)
    items = page.extract_items()
    for item in items:
        assert "url" in item
        assert "title" in item
        assert "price" in item
        assert "location" in item
        assert "description" in item


def test_extract_items_description_es_pending(mock_driver, search_results_html):
    page = make_page(mock_driver, search_results_html)
    items = page.extract_items()
    for item in items:
        assert item["description"] == "pending"


def test_extract_items_url_relativa_se_absolutifica(mock_driver, search_results_html):
    page = make_page(mock_driver, search_results_html)
    items = page.extract_items()
    # Los hrefs relativos (/item/...) deben ser absolutos
    items_con_url_relativa = [i for i in items if "/item/abc123" in i["url"]]
    assert len(items_con_url_relativa) == 1
    assert items_con_url_relativa[0]["url"].startswith("https://www.wallapop.com")


def test_extract_items_url_absoluta_sin_cambios(mock_driver, search_results_html):
    page = make_page(mock_driver, search_results_html)
    items = page.extract_items()
    # El href ya absoluto de ghi789 no debe duplicar el dominio
    items_ghi = [i for i in items if "ghi789" in i["url"]]
    assert len(items_ghi) == 1
    assert items_ghi[0]["url"] == "https://www.wallapop.com/item/ghi789"


def test_extract_items_max_items_respetado(mock_driver, search_results_html):
    page = make_page(mock_driver, search_results_html)
    items = page.extract_items(max_items=2)
    assert len(items) == 2


def test_extract_items_sin_cards_devuelve_vacio(mock_driver):
    page = make_page(mock_driver, "<div>Sin resultados</div>")
    items = page.extract_items()
    assert items == []


def test_extract_items_card_sin_href_ignorado(mock_driver):
    html = '<div><a class="item-card_ItemCard--abc">Sin href</a></div>'
    page = make_page(mock_driver, html)
    items = page.extract_items()
    assert items == []


def test_extract_items_titulo_correcto(mock_driver, search_results_html):
    page = make_page(mock_driver, search_results_html)
    items = page.extract_items()
    titulos = [i["title"] for i in items]
    assert "MacBook Pro M1" in titulos
    assert "iPhone 14 Pro" in titulos


def test_extract_items_precio_correcto(mock_driver, search_results_html):
    page = make_page(mock_driver, search_results_html)
    items = page.extract_items()
    macbook = next(i for i in items if i["title"] == "MacBook Pro M1")
    assert macbook["price"] == "800€"


def test_extract_items_sin_precio_devuelve_no_disponible(mock_driver, search_results_html):
    page = make_page(mock_driver, search_results_html)
    items = page.extract_items()
    # El teclado mecánico no tiene precio en el fixture
    teclado = next(i for i in items if i["title"] == "Teclado mecánico")
    assert teclado["price"] == "No disponible"
