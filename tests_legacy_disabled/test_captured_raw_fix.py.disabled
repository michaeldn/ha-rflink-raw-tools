from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components/rflink_raw/__init__.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"

def test_backend_returns_entity_candidates_and_raw_packets():
    init = INIT.read_text()
    assert "def _entity_candidates" in init
    assert "def _parse_rflink_packet" in init
    assert "'candidate_on'" in init
    assert "'candidate_off'" in init
    assert "'raw_packet'" in init
    assert "'send_candidate'" in init

def test_captured_page_explains_raw_and_shows_candidates():
    panel = PANEL.read_text()
    assert 'APP_BUILD_ID = "captured-raw-fix-20260511"' in panel
    assert "Raw RFLink packets" in panel
    assert "Candidate raw commands" in panel
    assert "RFLink device:" in panel
    assert "Raw RF capture logging" in panel

def test_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
