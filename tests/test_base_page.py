import pytest
from bs4 import BeautifulSoup
from src.pages.base_page import BasePage


def make_page(mock_driver):
    return BasePage(mock_driver, timeout=1)


def parse(html):
    return BeautifulSoup(html, "html.parser")


# ── find_by_class_pattern ────────────────────────────────────────────────────

def test_encuentra_elemento_por_substring_de_clase(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<span class="ItemCard__title--abc123">Título</span>')
    result = page.find_by_class_pattern(soup, "ItemCard__title")
    assert result is not None
    assert result.get_text() == "Título"


def test_devuelve_none_sin_match(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<span class="OtraClase--xyz">Texto</span>')
    result = page.find_by_class_pattern(soup, "ItemCard__title")
    assert result is None


def test_lista_de_patrones_primer_match(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<span class="ItemCard__price--abc">200€</span>')
    result = page.find_by_class_pattern(soup, ["no-match", "ItemCard__price"])
    assert result is not None
    assert result.get_text() == "200€"


def test_lista_de_patrones_todos_fallan_devuelve_none(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<span class="OtraClase">Texto</span>')
    result = page.find_by_class_pattern(soup, ["patron1", "patron2"])
    assert result is None


def test_lista_de_patrones_primer_match_gana(mock_driver):
    page = make_page(mock_driver)
    soup = parse(
        '<span class="primer-match--abc">A</span>'
        '<span class="segundo-match--xyz">B</span>'
    )
    result = page.find_by_class_pattern(soup, ["primer-match", "segundo-match"])
    assert result.get_text() == "A"


def test_elemento_anidado_profundo(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<div><div><div><span class="ItemCard__title--abc">Anidado</span></div></div></div>')
    result = page.find_by_class_pattern(soup, "ItemCard__title")
    assert result is not None
    assert result.get_text() == "Anidado"


def test_no_encuentra_elemento_sin_clase(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<div>Sin clase</div>')
    result = page.find_by_class_pattern(soup, "ItemCard__title")
    assert result is None


def test_match_parcial_con_multiples_clases(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<span class="foo ItemCard__title bar">Texto</span>')
    result = page.find_by_class_pattern(soup, "ItemCard__title")
    assert result is not None


# ── extract_from_pattern ─────────────────────────────────────────────────────

def test_extract_devuelve_texto_cuando_encuentra(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<span class="ItemCard__price--abc">199,99€</span>')
    result = page.extract_from_pattern(soup, "ItemCard__price")
    assert result == "199,99€"


def test_extract_devuelve_default_cuando_no_encuentra(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<span class="OtraClase">Texto</span>')
    result = page.extract_from_pattern(soup, "ItemCard__price")
    assert result == "No disponible"


def test_extract_devuelve_default_personalizado(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<span class="OtraClase">Texto</span>')
    result = page.extract_from_pattern(soup, "ItemCard__price", default="pending")
    assert result == "pending"


def test_extract_lista_de_patrones(mock_driver):
    page = make_page(mock_driver)
    soup = parse('<span class="location--xyz">Sevilla</span>')
    result = page.extract_from_pattern(soup, ["location", "distance"])
    assert result == "Sevilla"
