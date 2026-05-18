from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_tabs_only_turn_blue_while_pressed():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "pressed-tab-fix-20260511"' in text
    assert ".tab:active" in text
    assert "background:var(--primary-color)" in text
    assert "box-shadow:inset 0 0 0 1px var(--primary-color)" not in text
    assert ".tab.active{background:var(--primary-color)" not in text
    assert ".tab.active { background:var(--primary-color)" not in text
