from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_pre_restart_check_script_exists_and_explains_timing():
    text = (ROOT / "check-rflink-before-restart.sh").read_text()
    assert "BEFORE ha core restart" in text
    assert "PASS: no __pycache__ or *.pyc" in text

def test_install_runs_pre_restart_check():
    text = (ROOT / "install.sh").read_text()
    assert "Package cache check before cleanup" in text
    assert "Package cache check after cleanup" in text
    assert "sh /config/check-rflink-before-restart.sh" in text

def test_no_cache_artifacts_in_package():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
