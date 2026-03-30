import pytest
from unittest.mock import MagicMock, patch, call
from src.scraper import WallapopScraper


def make_scraper(mock_driver):
    scraper = WallapopScraper(headless=True)
    scraper.driver = mock_driver
    return scraper


# ── _is_driver_alive ──────────────────────────────────────────────────────────

def test_driver_alive_cuando_responde(mock_driver):
    scraper = make_scraper(mock_driver)
    mock_driver.execute_script.return_value = 1
    assert scraper._is_driver_alive() is True


def test_driver_alive_false_cuando_lanza_excepcion(mock_driver):
    scraper = make_scraper(mock_driver)
    mock_driver.execute_script.side_effect = Exception("Sesión cerrada")
    assert scraper._is_driver_alive() is False


def test_driver_alive_false_cuando_driver_es_none():
    scraper = WallapopScraper(headless=True)
    scraper.driver = None
    assert scraper._is_driver_alive() is False


# ── _enrich_items_with_recovery ───────────────────────────────────────────────

def _make_item(i, description="Descripción real"):
    return {
        "url": f"https://wallapop.com/item/{i}",
        "title": f"Item {i}",
        "price": "100€",
        "location": "Madrid",
        "description": description,
    }


def _mock_detail_page(mocker, return_items):
    """Mockea ItemDetailPage para devolver los items en orden."""
    iter_items = iter(return_items)

    def enrich_side_effect(item):
        return next(iter_items)

    mock_cls = mocker.patch("src.scraper.ItemDetailPage")
    mock_instance = MagicMock()
    mock_instance.enrich_item.side_effect = enrich_side_effect
    mock_cls.return_value = mock_instance
    return mock_cls, mock_instance


def test_enrich_enriquece_todos_los_items(mocker, mock_driver):
    items = [_make_item(i) for i in range(3)]
    _, mock_detail = _mock_detail_page(mocker, items)
    mocker.patch("time.sleep")

    scraper = make_scraper(mock_driver)
    scraper._is_driver_alive = MagicMock(return_value=True)
    scraper._restart_driver = MagicMock()

    result = scraper._enrich_items_with_recovery(items, timeout=1)
    assert len(result) == 3
    assert mock_detail.enrich_item.call_count == 3


def test_enrich_reinicia_driver_si_muerto(mocker, mock_driver):
    items = [_make_item(i) for i in range(3)]
    _, mock_detail = _mock_detail_page(mocker, items)
    mocker.patch("time.sleep")

    scraper = make_scraper(mock_driver)
    # Driver muerto en el segundo item
    scraper._is_driver_alive = MagicMock(side_effect=[True, False, True])
    scraper._restart_driver = MagicMock()

    scraper._enrich_items_with_recovery(items, timeout=1)
    scraper._restart_driver.assert_called_once()


def test_enrich_reinicia_tras_tres_fallos_consecutivos(mocker, mock_driver):
    # 3 items con description "No disponible" (fallos)
    items_fallidos = [_make_item(i, description="No disponible") for i in range(3)]
    _, mock_detail = _mock_detail_page(mocker, items_fallidos)
    mocker.patch("time.sleep")

    scraper = make_scraper(mock_driver)
    scraper._is_driver_alive = MagicMock(return_value=True)
    scraper._restart_driver = MagicMock()

    scraper._enrich_items_with_recovery(items_fallidos, timeout=1)
    scraper._restart_driver.assert_called_once()


def test_enrich_contador_fallos_se_resetea_con_exito(mocker, mock_driver):
    # 2 fallos, 1 éxito: no debe llegar a 3 consecutivos
    items = [
        _make_item(0, description="No disponible"),
        _make_item(1, description="No disponible"),
        _make_item(2, description="Descripción real"),  # éxito: resetea contador
    ]
    _, mock_detail = _mock_detail_page(mocker, items)
    mocker.patch("time.sleep")

    scraper = make_scraper(mock_driver)
    scraper._is_driver_alive = MagicMock(return_value=True)
    scraper._restart_driver = MagicMock()

    scraper._enrich_items_with_recovery(items, timeout=1)
    scraper._restart_driver.assert_not_called()


def test_enrich_batch_restart_en_batch_size(mocker, mock_driver):
    batch_size = WallapopScraper.BATCH_SIZE  # 25
    # 26 items para forzar un reinicio de batch en índice 25
    items = [_make_item(i) for i in range(batch_size + 1)]
    _, mock_detail = _mock_detail_page(mocker, items)
    mocker.patch("time.sleep")

    scraper = make_scraper(mock_driver)
    scraper._is_driver_alive = MagicMock(return_value=True)
    scraper._restart_driver = MagicMock()

    scraper._enrich_items_with_recovery(items, timeout=1)
    # Debe reiniciar exactamente una vez (al llegar a i=25)
    assert scraper._restart_driver.call_count == 1


def test_enrich_anti_detection_delay_n_menos_1_veces(mocker, mock_driver):
    n = 4
    items = [_make_item(i) for i in range(n)]
    _, mock_detail = _mock_detail_page(mocker, items)
    mock_sleep = mocker.patch("time.sleep")

    scraper = make_scraper(mock_driver)
    scraper._is_driver_alive = MagicMock(return_value=True)
    scraper._restart_driver = MagicMock()

    scraper._enrich_items_with_recovery(items, timeout=1)
    # anti_detection_delay llama a time.sleep una vez, y hay N-1 delays
    # (también puede haber sleep en _restart_driver, pero no se llama aquí)
    assert mock_sleep.call_count == n - 1
