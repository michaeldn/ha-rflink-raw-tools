"""Persistent settings and dashboard helpers for RFLink Raw Tools."""

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


def _storage_dir(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(".storage"))


def _default_lovelace_path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(".storage/lovelace"))


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


def _dashboard_card_yaml() -> str:
    """Return a safe, user-copyable dashboard shortcut card."""
    return (
        "type: button\n"
        "name: RFLink Raw Tools\n"
        "icon: mdi:radio-tower\n"
        "show_name: true\n"
        "show_icon: true\n"
        "tap_action:\n"
        "  action: navigate\n"
        "  navigation_path: /rflink-raw-tools\n"
    )


def _write_fallback_card(hass: HomeAssistant) -> dict[str, Any]:
    """Write the copyable card YAML as a convenience file only."""
    snippet = _home_card_path(hass)
    snippet.write_text(_dashboard_card_yaml())
    return {
        "ok": True,
        "changed": True,
        "path": str(snippet),
        "message": (
            "Dashboard auto-editing was removed in v0.0.5. "
            "Copy the dashboard shortcut YAML from Configuration and paste it into a Manual card. "
            f"A copy was also written to {snippet}."
        ),
    }


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
        return options

    await hass.async_add_executor_job(_set)
    return await async_get_options(hass)


async def async_install_home_card(hass: HomeAssistant) -> dict[str, Any]:
    """Compatibility no-op.

    Automatic Overview dashboard editing was removed in v0.0.5 because Home Assistant's
    automatic Overview dashboard is not reliably writable by custom integrations.
    """
    try:
        options = await async_set_options(hass, {"home_card_enabled": False})
    except Exception:
        options = {}
    return {
        "ok": True,
        "changed": False,
        "options": options,
        "message": (
            "Automatic Overview dashboard editing was removed in v0.0.5. "
            "Use Configuration -> Dashboard shortcut -> Copy card YAML, then paste it into a Manual card."
        ),
    }


async def async_remove_home_card(hass: HomeAssistant) -> dict[str, Any]:
    """Compatibility no-op.

    Automatic Overview dashboard editing was removed in v0.0.5.
    """
    try:
        options = await async_set_options(hass, {"home_card_enabled": False})
    except Exception:
        options = {}
    return {
        "ok": True,
        "changed": False,
        "options": options,
        "message": "Automatic Overview dashboard editing was removed in v0.0.5.",
    }
