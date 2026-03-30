import csv
import pytest
from bs4 import BeautifulSoup
from src.utils import extract_text_safe, save_to_csv


# ── extract_text_safe ────────────────────────────────────────────────────────

def test_extract_none_devuelve_default():
    assert extract_text_safe(None) == "No disponible"


def test_extract_none_default_personalizado():
    assert extract_text_safe(None, default="pending") == "pending"


def test_extract_elemento_con_texto():
    soup = BeautifulSoup('<span class="foo">  Hola mundo  </span>', "html.parser")
    elem = soup.find("span")
    assert extract_text_safe(elem) == "Hola mundo"


def test_extract_elemento_con_etiquetas_anidadas():
    soup = BeautifulSoup("<div><b>Negrita</b> y <i>cursiva</i></div>", "html.parser")
    elem = soup.find("div")
    text = extract_text_safe(elem)
    assert "Negrita" in text
    assert "cursiva" in text


def test_extract_elemento_solo_espacios_devuelve_default():
    soup = BeautifulSoup("<span>   </span>", "html.parser")
    elem = soup.find("span")
    assert extract_text_safe(elem) == "No disponible"


def test_extract_elemento_vacio_devuelve_default():
    soup = BeautifulSoup("<span></span>", "html.parser")
    elem = soup.find("span")
    assert extract_text_safe(elem) == "No disponible"


# ── save_to_csv ──────────────────────────────────────────────────────────────

def test_save_csv_lista_vacia_devuelve_false(tmp_path):
    assert save_to_csv([], "test.csv", str(tmp_path)) is False


def test_save_csv_crea_fichero(tmp_path):
    items = [{"url": "https://wallapop.com/item/1", "title": "Test", "price": "100€",
              "description": "desc", "location": "Madrid"}]
    result = save_to_csv(items, "test.csv", str(tmp_path))
    assert result is True
    assert (tmp_path / "test.csv").exists()


def test_save_csv_cabeceras_correctas(tmp_path):
    items = [{"url": "u", "title": "t", "price": "p", "description": "d", "location": "l"}]
    save_to_csv(items, "test.csv", str(tmp_path))
    with open(tmp_path / "test.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["url", "title", "price", "description", "location"]


def test_save_csv_rellena_campos_faltantes(tmp_path):
    items = [{"url": "https://wallapop.com/item/1"}]
    save_to_csv(items, "test.csv", str(tmp_path))
    with open(tmp_path / "test.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        row = next(reader)
    assert row["title"] == "No disponible"
    assert row["price"] == "No disponible"
    assert row["description"] == "No disponible"
    assert row["location"] == "No disponible"


def test_save_csv_devuelve_true_con_exito(tmp_path):
    items = [{"url": "u", "title": "t", "price": "p", "description": "d", "location": "l"}]
    assert save_to_csv(items, "test.csv", str(tmp_path)) is True


def test_save_csv_multiples_items(tmp_path):
    items = [
        {"url": f"https://wallapop.com/item/{i}", "title": f"Item {i}",
         "price": f"{i*10}€", "description": "desc", "location": "Madrid"}
        for i in range(5)
    ]
    save_to_csv(items, "test.csv", str(tmp_path))
    with open(tmp_path / "test.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5
