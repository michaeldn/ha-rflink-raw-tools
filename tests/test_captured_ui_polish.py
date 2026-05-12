from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_captured_page_uses_polished_card_layout():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "captured-ui-polish-20260511"' in text
    assert "captured-layout" in text
    assert "entity-grid" in text
    assert "entity-card" in text
    assert "raw-panel" in text
    assert "command-row" in text
    assert "command candidates" in text

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
