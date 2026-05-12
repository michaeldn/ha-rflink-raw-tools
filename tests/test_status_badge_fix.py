from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_status_badge_updates_after_status_load():
    text = PANEL.read_text()
    assert 'APP_BUILD_ID = "status-badge-fix-20260512"' in text
    assert 'id="status-badge"' in text
    assert "_updateStatusBadge(" in text
    assert "this._updateStatusBadge();" in text
    assert "badge.innerHTML=this._statusBadge()" in text or "badge.innerHTML = this._statusBadge()" in text
    assert "● Checking RFLink…" not in text

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
