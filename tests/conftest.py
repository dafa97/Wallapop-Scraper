import json
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import MagicMock

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ── Database fixture ────────────────────────────────────────────────────────

@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Redirige la DB a un directorio temporal y la inicializa."""
    import src.database as db_module
    monkeypatch.setattr(db_module, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(db_module, "DB_NAME", "test.db")
    db_module.init_db()
    return tmp_path / "test.db"


# ── searches.json fixture ────────────────────────────────────────────────────

@pytest.fixture
def searches_file(tmp_path, monkeypatch):
    """Crea un searches.json temporal y lo parchea en api y scheduler."""
    path = tmp_path / "searches.json"
    path.write_text('{"searches": []}', encoding="utf-8")

    import src.api as api_module
    monkeypatch.setattr(api_module, "SEARCHES_FILE", str(path))

    import src.scheduler as scheduler_module
    monkeypatch.setattr(scheduler_module, "SEARCHES_FILE", path)

    return path


# ── API client fixture ───────────────────────────────────────────────────────

@pytest.fixture
def api_client(db_path, searches_file):
    """TestClient de FastAPI con DB y searches.json temporales."""
    from fastapi.testclient import TestClient
    from src.api import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_active_scrapes():
    """Limpia el estado de scrapes entre tests para evitar estado compartido."""
    import src.events as ev
    ev._active_scrapes.clear()
    ev._scrape_events.clear()
    yield
    ev._active_scrapes.clear()
    ev._scrape_events.clear()


# ── Mock driver fixture ──────────────────────────────────────────────────────

@pytest.fixture
def mock_driver():
    """Driver de Selenium simulado."""
    driver = MagicMock()
    driver.page_source = ""
    driver.execute_script.return_value = 1
    return driver


# ── HTML fixture helpers ─────────────────────────────────────────────────────

@pytest.fixture
def search_results_html():
    return (FIXTURES_DIR / "search_results.html").read_text(encoding="utf-8")


@pytest.fixture
def item_detail_html():
    return (FIXTURES_DIR / "item_detail.html").read_text(encoding="utf-8")
