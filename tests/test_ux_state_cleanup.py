from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components/rflink_raw/__init__.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_backend_sanitizes_unknown_command_status():
    text = INIT.read_text()
    assert "def _sanitize_status_data" in text
    assert "_sanitize_status_data(hass)" in text
    assert "Unknown command" in text

def test_frontend_capture_and_debug_labels():
    text = PANEL.read_text()
    assert 'data-tab="capture">Capture' in text
    assert "Capture a remote command" in text
    assert "Decoded RFLink logging" in text
    assert "Raw RF capture logging" in text
    assert "_debugEnabled" in text
    assert "_autoClearStaleUnknown" in text
    assert 'APP_BUILD_ID = "ux-state-cleanup-fix-20260510"' in text
