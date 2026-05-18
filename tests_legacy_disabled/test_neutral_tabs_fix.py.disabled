from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_active_tab_is_not_solid_blue():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "neutral-tabs-fix-20260511"' in text
    assert '.tab.active{background:var(--secondary-background-color);color:var(--primary-text-color);border-color:var(--primary-color);box-shadow:inset 0 0 0 1px var(--primary-color)}' in text or '.tab.active { background:var(--secondary-background-color); color:var(--primary-text-color); border-color:var(--primary-color); box-shadow:inset 0 0 0 1px var(--primary-color); }' in text
    assert '.tab.active{background:var(--primary-color);color:var(--text-primary-color' not in text
    assert '.tab.active { background:var(--primary-color); color:var(--text-primary-color' not in text
