import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components/rflink_raw/__init__.py"
PANEL = ROOT / "custom_components/rflink_raw/www/rflink-raw-tools-panel.js"


def test_async_setup_structure_and_backend_registration():
    tree = ast.parse(INIT.read_text())
    top_level_async = {node.name for node in tree.body if isinstance(node, ast.AsyncFunctionDef)}

    assert "async_setup" in top_level_async
    assert "async_setup_entry" in top_level_async
    assert "_async_register_backend" in top_level_async

    async_setup = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup")
    setup_entry = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup_entry")

    assert "_async_register_backend" in ast.unparse(async_setup)
    assert "_async_register_backend" in ast.unparse(setup_entry)
    assert any(isinstance(node, ast.Return) and isinstance(node.value, ast.Constant) and node.value.value is True for node in ast.walk(async_setup))


def test_frontend_debug_switches_and_no_ping_default():
    text = PANEL.read_text()
    assert 'data-toggle-debug="rfdebug"' in text
    assert 'data-toggle-debug="qrfdebug"' in text
    assert '|| "10;PING;"' not in text
    assert "10;NewKaku;01a2b3;1;ON;" in text
