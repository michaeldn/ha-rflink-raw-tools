from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_captured_css_is_bundled():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "captured-css-fix-20260511"' in text
    style = text.split("<style>", 1)[1].split("</style>", 1)[0]
    for snippet in [
        ".captured-layout",
        ".hero-row",
        ".stat-row",
        ".captured-columns",
        ".entity-grid",
        ".entity-card",
        ".raw-panel",
        ".command-row",
        ".empty-state",
    ]:
        assert snippet in style

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
