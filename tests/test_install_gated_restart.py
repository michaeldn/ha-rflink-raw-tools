from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "install.sh"
PRECHECK = ROOT / "check-rflink-before-restart.sh"

def test_install_gates_restart_with_checks():
    text = INSTALL.read_text()
    assert "has_cache_artifacts()" in text
    assert "grep -q ." in text
    assert "if ! sh /config/check-rflink-before-restart.sh" in text
    assert "fail " in text
    assert "ha core restart" in text
    assert text.rfind("ha core restart") > text.rfind("All pre-restart checks passed.")

def test_precheck_exits_nonzero_on_cache_artifacts():
    text = PRECHECK.read_text()
    assert "grep -q ." in text
    assert "exit 2" in text
    assert "PASS: no __pycache__ or *.pyc" in text

def test_no_cache_artifacts_in_package():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
