from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_current_tab_is_blue_and_state_updates():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "active-tab-state-fix-20260511"' in text
    assert "_updateTabs(" in text
    assert "classList.toggle('active',b.dataset.tab===this._state.tab)" in text or 'classList.toggle("active", btn.dataset.tab === this._state.tab)' in text
    assert "this._updateTabs();" in text
    assert ".tab.active" in text
    assert "background:var(--primary-color)" in text
    assert "box-shadow:inset 0 0 0 1px var(--primary-color)" not in text
