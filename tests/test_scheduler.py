import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from src.scheduler import _load_searches, Scheduler


# ── _load_searches ───────────────────────────────────────────────────────────

def test_load_searches_fichero_valido(tmp_path):
    path = tmp_path / "searches.json"
    path.write_text(
        json.dumps({"searches": [{"query": "MacBook", "interval_minutes": 30}]}),
        encoding="utf-8"
    )
    result = _load_searches(path)
    assert len(result) == 1
    assert result[0]["query"] == "MacBook"


def test_load_searches_fichero_inexistente(tmp_path):
    result = _load_searches(tmp_path / "no_existe.json")
    assert result == []


def test_load_searches_json_invalido(tmp_path):
    path = tmp_path / "searches.json"
    path.write_text("esto no es json", encoding="utf-8")
    result = _load_searches(path)
    assert result == []


def test_load_searches_clave_ausente(tmp_path):
    path = tmp_path / "searches.json"
    path.write_text(json.dumps({"otro": []}), encoding="utf-8")
    result = _load_searches(path)
    assert result == []


def test_load_searches_lista_vacia(tmp_path):
    path = tmp_path / "searches.json"
    path.write_text(json.dumps({"searches": []}), encoding="utf-8")
    result = _load_searches(path)
    assert result == []


# ── Scheduler._reload_config_if_needed ───────────────────────────────────────

def test_reload_carga_en_primera_llamada(mocker, tmp_path):
    path = tmp_path / "searches.json"
    path.write_text(
        json.dumps({"searches": [{"query": "iPhone", "interval_minutes": 60}]}),
        encoding="utf-8"
    )
    mock_load = mocker.patch(
        "src.scheduler._load_searches",
        return_value=[{"query": "iPhone", "interval_minutes": 60}]
    )
    scheduler = Scheduler()
    scheduler._reload_config_if_needed()
    mock_load.assert_called_once()
    assert scheduler._searches == [{"query": "iPhone", "interval_minutes": 60}]


def test_reload_no_recarga_dentro_del_intervalo(mocker):
    mock_load = mocker.patch(
        "src.scheduler._load_searches",
        return_value=[{"query": "iPhone", "interval_minutes": 60}]
    )
    scheduler = Scheduler()
    scheduler._last_config_load = datetime.now()  # Recién cargado
    scheduler._reload_config_if_needed()
    mock_load.assert_not_called()


def test_reload_recarga_tras_intervalo_expirado(mocker):
    mock_load = mocker.patch(
        "src.scheduler._load_searches",
        return_value=[{"query": "iPhone", "interval_minutes": 60}]
    )
    scheduler = Scheduler()
    scheduler._last_config_load = datetime.now() - timedelta(seconds=400)
    scheduler._reload_config_if_needed()
    mock_load.assert_called_once()


def test_reload_nueva_busqueda_se_programa_inmediatamente(mocker):
    scheduler = Scheduler()
    scheduler._searches = [{"query": "MacBook", "interval_minutes": 60}]
    scheduler._last_config_load = datetime.now() - timedelta(seconds=400)

    mocker.patch(
        "src.scheduler._load_searches",
        return_value=[
            {"query": "MacBook", "interval_minutes": 60},
            {"query": "iPhone", "interval_minutes": 30},
        ]
    )

    before = datetime.now()
    scheduler._reload_config_if_needed()
    after = datetime.now()

    assert "iPhone" in scheduler._next_run
    assert before <= scheduler._next_run["iPhone"] <= after


def test_reload_busqueda_existente_no_resetea_next_run(mocker):
    scheduler = Scheduler()
    scheduler._searches = [{"query": "MacBook", "interval_minutes": 60}]
    future = datetime.now() + timedelta(minutes=30)
    scheduler._next_run["MacBook"] = future
    scheduler._last_config_load = datetime.now() - timedelta(seconds=400)

    mocker.patch(
        "src.scheduler._load_searches",
        return_value=[{"query": "MacBook", "interval_minutes": 60}]
    )

    scheduler._reload_config_if_needed()
    assert scheduler._next_run["MacBook"] == future


# ── Scheduler._process_searches ──────────────────────────────────────────────

def test_process_ejecuta_busqueda_cuando_toca(mocker):
    mock_run = mocker.patch("src.scheduler._run_single_search")
    scheduler = Scheduler()
    scheduler._searches = [{"query": "MacBook", "interval_minutes": 60}]
    scheduler._next_run["MacBook"] = datetime.now() - timedelta(seconds=1)

    scheduler._process_searches()
    mock_run.assert_called_once_with("MacBook")


def test_process_no_ejecuta_busqueda_futura(mocker):
    mock_run = mocker.patch("src.scheduler._run_single_search")
    scheduler = Scheduler()
    scheduler._searches = [{"query": "MacBook", "interval_minutes": 60}]
    scheduler._next_run["MacBook"] = datetime.now() + timedelta(minutes=30)

    scheduler._process_searches()
    mock_run.assert_not_called()


def test_process_stop_event_evita_ejecucion(mocker):
    mock_run = mocker.patch("src.scheduler._run_single_search")
    scheduler = Scheduler()
    scheduler._searches = [{"query": "MacBook", "interval_minutes": 60}]
    scheduler._next_run["MacBook"] = datetime.now() - timedelta(seconds=1)
    scheduler.stop()

    scheduler._process_searches()
    mock_run.assert_not_called()


def test_process_programa_siguiente_run(mocker):
    mocker.patch("src.scheduler._run_single_search")
    scheduler = Scheduler()
    scheduler._searches = [{"query": "MacBook", "interval_minutes": 60}]
    scheduler._next_run["MacBook"] = datetime.now() - timedelta(seconds=1)

    before = datetime.now()
    scheduler._process_searches()
    after = datetime.now()

    expected_min = before + timedelta(minutes=60)
    expected_max = after + timedelta(minutes=60)
    assert expected_min <= scheduler._next_run["MacBook"] <= expected_max


def test_process_primera_ejecucion_sin_next_run(mocker):
    mock_run = mocker.patch("src.scheduler._run_single_search")
    scheduler = Scheduler()
    scheduler._searches = [{"query": "MacBook", "interval_minutes": 60}]
    # Sin entry en _next_run: debe ejecutarse inmediatamente

    scheduler._process_searches()
    mock_run.assert_called_once_with("MacBook")


# ── Scheduler.running ─────────────────────────────────────────────────────────

def test_running_true_antes_de_stop():
    scheduler = Scheduler()
    assert scheduler.running is True


def test_running_false_despues_de_stop():
    scheduler = Scheduler()
    scheduler.stop()
    assert scheduler.running is False
