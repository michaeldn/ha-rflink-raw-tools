from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
CONST = ROOT / "custom_components/rflink_raw/const.py"

def test_app_build_not_visible_in_ui():
    panel = PANEL.read_text()
    assert "App build" not in panel
    assert 'APP_BUILD_ID = "hide-app-build-20260511"' in panel

def test_cache_busting_still_exists():
    const = CONST.read_text()
    assert 'PANEL_BUILD = "hide-app-build-20260511"' in const
    assert "?v={PANEL_BUILD}" in const

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
