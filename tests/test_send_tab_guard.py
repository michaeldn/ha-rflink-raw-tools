from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"


def test_send_tab_guards_ping_version_and_clears_stale_storage():
    text = PANEL.read_text()
    assert "_rawCommandKind(raw)" in text
    assert 'kind === "ping"' in text
    assert 'kind === "version"' in text
    assert 'ping_gateway' in text
    assert 'version_gateway' in text
    assert "_migrateOldSavedCommand" in text
    assert "_clearRawCommand" in text
    assert '|| "10;PING;"' not in text
