from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_check_script_mentions_runtime_cache_is_expected():
    text = (ROOT / "check-rflink-app-build.sh").read_text()
    assert "normal runtime bytecode" in text
    assert "They may return after another Core restart" in text

def test_cleanup_script_exists():
    text = (ROOT / "clean-rflink-runtime-cache.sh").read_text()
    assert "__pycache__" in text
    assert "*.pyc" in text

def test_package_source_has_no_cache_artifacts():
    assert not list(ROOT.rglob("__pycache__"))
    assert not list(ROOT.rglob("*.pyc"))
