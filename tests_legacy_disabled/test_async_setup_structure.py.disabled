import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components/rflink_raw/__init__.py"


def _module():
    return ast.parse(INIT.read_text())


def test_async_setup_top_level_return_true_and_no_leaked_service_handlers():
    tree = _module()
    top_level_async = {
        node.name for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
    }

    assert "async_setup" in top_level_async
    assert "async_setup_entry" in top_level_async
    assert "async_unload_entry" in top_level_async

    # These service handlers must be nested inside async_setup, not leaked at module scope.
    assert "ping_gateway" not in top_level_async
    assert "version_gateway" not in top_level_async
    assert "set_debug" not in top_level_async

    async_setup = next(
        node for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup"
    )

    assert any(
        isinstance(node, ast.Return)
        and isinstance(node.value, ast.Constant)
        and node.value.value is True
        for node in ast.walk(async_setup)
    )

    nested_handlers = {
        node.name for node in async_setup.body if isinstance(node, ast.AsyncFunctionDef)
    }
    assert {"send_raw", "send_protocol", "ping_gateway", "version_gateway", "set_debug"}.issubset(nested_handlers)
