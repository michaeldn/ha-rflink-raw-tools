from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components/rflink_raw/__init__.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
SERVICES = ROOT / "custom_components/rflink_raw/services.yaml"

def test_clear_status_backend_and_service():
    init = INIT.read_text()
    services = SERVICES.read_text()
    assert "def _clear_status_data" in init
    assert "def _clear_stale_unknown_command" in init
    assert '"clear_status"' in init
    assert "clear_status:" in services

def test_status_load_does_not_replay_backend_error_banner():
    panel = PANEL.read_text()
    assert "Status load should not replay old backend errors" in panel
    assert "status.last_error ||" not in panel.split("async _loadStatus", 1)[1].split("_formatError", 1)[0]
    assert 'data-action="_clearStatus"' in panel
    assert "Last backend error" in panel
