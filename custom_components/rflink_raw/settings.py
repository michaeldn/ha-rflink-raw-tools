"""Persistent settings for RFLink Raw Tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

SIGNAL_OPTIONS_UPDATED = "rflink_raw_options_updated"
OPTIONS_FILE = "rflink_raw_options.json"
HOME_CARD_FILE = "rflink_raw_home_card.yaml"

DEFAULT_OPTIONS: dict[str, bool] = {
    "sidebar_enabled": True,
    "alias_switches_enabled": True,
    "home_card_enabled": False,
}


def _options_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(OPTIONS_FILE))


def _home_card_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(HOME_CARD_FILE))


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _normalize(data: dict[str, Any]) -> dict[str, bool]:
    options = dict(DEFAULT_OPTIONS)
    for key in DEFAULT_OPTIONS:
        if key in data:
            options[key] = bool(data[key])
    return options


def _write(path: Path, options: dict[str, bool]) -> None:
    path.write_text(json.dumps(_normalize(options), indent=2, sort_keys=True) + "\n")


async def async_get_options(hass: HomeAssistant) -> dict[str, bool]:
    options = await hass.async_add_executor_job(_read, _options_path(hass))
    normalized = _normalize(options)
    normalized["home_card_installed"] = _home_card_path(hass).exists()
    return normalized


async def async_set_options(hass: HomeAssistant, updates: dict[str, Any]) -> dict[str, bool]:
    def _set() -> dict[str, bool]:
        path = _options_path(hass)
        options = _normalize(_read(path))
        for key in DEFAULT_OPTIONS:
            if key in updates:
                options[key] = bool(updates[key])
        _write(path, options)
        options["home_card_installed"] = _home_card_path(hass).exists()
        return options

    return await hass.async_add_executor_job(_set)


async def async_install_home_card(hass: HomeAssistant) -> dict[str, Any]:
    """Write a reusable Lovelace card snippet without editing dashboards automatically."""

    def _install() -> dict[str, Any]:
        path = _home_card_path(hass)
        content = """# RFLink Raw Tools Home card\n# RFLink Raw Tools Home screen card.\ntype: markdown\ntitle: RFLink Raw Tools\ncontent: >\n  [Open RFLink Raw Tools](/rflink-raw-tools) to capture remotes, send learned RFLink commands,\n  and manage Teach/Alias switches.\n"""
        path.write_text(content)
        options = _normalize(_read(_options_path(hass)))
        options["home_card_enabled"] = True
        _write(_options_path(hass), options)
        return {"ok": True, "changed": True, "path": str(path), "message": "RFLink Raw Tools Home screen card is ready for the Overview dashboard."}

    return await hass.async_add_executor_job(_install)


async def async_remove_home_card(hass: HomeAssistant) -> dict[str, Any]:
    """Remove the generated Home card snippet."""

    def _remove() -> dict[str, Any]:
        path = _home_card_path(hass)
        changed = False
        if path.exists():
            path.unlink()
            changed = True
        options = _normalize(_read(_options_path(hass)))
        options["home_card_enabled"] = False
        _write(_options_path(hass), options)
        return {"ok": True, "changed": changed, "path": str(path), "message": "Removed RFLink Raw Tools Home screen card." if changed else "No RFLink Raw Tools Home screen card was installed."}

    return await hass.async_add_executor_job(_remove)
