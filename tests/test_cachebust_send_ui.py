from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONST = ROOT / "custom_components/rflink_raw/const.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_frontend_cachebust_and_send_ui():
    const = CONST.read_text()
    panel = PANEL.read_text()
    assert "PANEL_BUILD" in const
    assert "?v={PANEL_BUILD}" in const
    assert "APP_BUILD_ID" in panel
    assert "_clearRawCommand" in panel
    assert 'data-action="_clearRawCommand"' in panel
    assert "_migrateOldSavedCommand" in panel
    assert "_rawCommandKind(raw)" in panel
    assert '10;Chuango;example;ON;' not in panel
    assert '|| "10;PING;"' not in panel
