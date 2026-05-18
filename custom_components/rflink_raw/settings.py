"""Persistent settings and dashboard helpers for RFLink Raw Tools."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
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


def _lovelace_path(hass: HomeAssistant) -> Path:
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


def _overview_card() -> dict[str, Any]:
    return {
        "type": "button",
        "name": "RFLink Raw Tools",
        "icon": "mdi:radio-tower",
        "show_name": True,
        "show_icon": True,
        "tap_action": {"action": "navigate", "navigation_path": "/rflink-raw-tools"},
        "hold_action": {"action": "none"},
    }


def _is_rflink_card(card: Any) -> bool:
    if not isinstance(card, dict):
        return False
    tap = card.get("tap_action")
    nav = tap.get("navigation_path") if isinstance(tap, dict) else ""
    if nav == "/rflink-raw-tools":
        return True
    text = json.dumps(card, sort_keys=True)
    return "rflink-raw-tools" in text or "RFLink Raw Tools" in text


def _find_config(data: dict[str, Any]) -> dict[str, Any]:
    inner = data.setdefault("data", {})
    if "config" in inner and isinstance(inner["config"], dict):
        return inner["config"]
    if "views" in inner and isinstance(inner["views"], list):
        return inner
    config = inner.setdefault("config", {})
    if not isinstance(config, dict):
        inner["config"] = {}
        config = inner["config"]
    return config


def _first_view(config: dict[str, Any]) -> dict[str, Any]:
    views = config.setdefault("views", [])
    if not isinstance(views, list):
        config["views"] = []
        views = config["views"]
    if not views:
        views.append({"title": "Home", "path": "default_view", "cards": []})
    if not isinstance(views[0], dict):
        views[0] = {"title": "Home", "path": "default_view", "cards": []}
    return views[0]


def _card_containers(view: dict[str, Any]) -> list[list[Any]]:
    containers: list[list[Any]] = []
    cards = view.setdefault("cards", [])
    if isinstance(cards, list):
        containers.append(cards)
    sections = view.get("sections")
    if isinstance(sections, list):
        for section in sections:
            if isinstance(section, dict):
                section_cards = section.setdefault("cards", [])
                if isinstance(section_cards, list):
                    containers.append(section_cards)
    return containers


def _install_overview_card(hass: HomeAssistant) -> dict[str, Any]:
    lovelace = _lovelace_path(hass)
    if not lovelace.exists():
        snippet = _home_card_path(hass)
        snippet.write_text(
            "type: button\n"
            "name: RFLink Raw Tools\n"
            "icon: mdi:radio-tower\n"
            "tap_action:\n"
            "  action: navigate\n"
            "  navigation_path: /rflink-raw-tools\n"
        )
        return {"ok": False, "changed": True, "path": str(snippet), "message": "Default Overview dashboard storage was not found. Wrote a fallback RFLink card file instead."}

    backup = lovelace.with_name(f"{lovelace.name}.rflink_raw_tools_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(lovelace, backup)

    data = json.loads(lovelace.read_text())
    config = _find_config(data)
    view = _first_view(config)
    containers = _card_containers(view)
    if not containers:
        view["cards"] = []
        containers = [view["cards"]]

    for cards in containers:
        if any(_is_rflink_card(card) for card in cards):
            return {"ok": True, "changed": False, "backup": str(backup), "message": "RFLink Raw Tools is already on the Overview dashboard."}

    containers[0].append(_overview_card())
    lovelace.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")
    return {"ok": True, "changed": True, "backup": str(backup), "message": "Added RFLink Raw Tools to the Overview dashboard. Refresh Overview if it is already open."}


def _remove_overview_card(hass: HomeAssistant) -> dict[str, Any]:
    lovelace = _lovelace_path(hass)
    changed = False
    if lovelace.exists():
        backup = lovelace.with_name(f"{lovelace.name}.rflink_raw_tools_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(lovelace, backup)
        data = json.loads(lovelace.read_text())
        config = _find_config(data)
        views = config.get("views", [])
        if isinstance(views, list):
            for view in views:
                if not isinstance(view, dict):
                    continue
                for cards in _card_containers(view):
                    before = len(cards)
                    cards[:] = [card for card in cards if not _is_rflink_card(card)]
                    changed = changed or (len(cards) != before)
        if changed:
            lovelace.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")
        return {"ok": True, "changed": changed, "backup": str(backup), "message": "Removed RFLink Raw Tools from the Overview dashboard." if changed else "No RFLink Raw Tools Overview dashboard card was found."}

    snippet = _home_card_path(hass)
    if snippet.exists():
        snippet.unlink()
        changed = True
    return {"ok": True, "changed": changed, "message": "Removed RFLink Raw Tools Home card file." if changed else "No RFLink Raw Tools Overview dashboard card was found."}


async def async_get_options(hass: HomeAssistant) -> dict[str, bool]:
    options = await hass.async_add_executor_job(_read, _options_path(hass))
    normalized = _normalize(options)

    def _installed() -> bool:
        lovelace = _lovelace_path(hass)
        if lovelace.exists():
            try:
                data = json.loads(lovelace.read_text())
                config = _find_config(data)
                views = config.get("views", [])
                if isinstance(views, list):
                    for view in views:
                        if isinstance(view, dict):
                            for cards in _card_containers(view):
                                if any(_is_rflink_card(card) for card in cards):
                                    return True
            except Exception:
                return False
        return _home_card_path(hass).exists()

    normalized["home_card_installed"] = await hass.async_add_executor_job(_installed)
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
    def _install() -> dict[str, Any]:
        result = _install_overview_card(hass)
        options = _normalize(_read(_options_path(hass)))
        options["home_card_enabled"] = bool(result.get("ok", True))
        _write(_options_path(hass), options)
        return result

    return await hass.async_add_executor_job(_install)


async def async_remove_home_card(hass: HomeAssistant) -> dict[str, Any]:
    def _remove() -> dict[str, Any]:
        result = _remove_overview_card(hass)
        options = _normalize(_read(_options_path(hass)))
        options["home_card_enabled"] = False
        _write(_options_path(hass), options)
        return result

    return await hass.async_add_executor_job(_remove)
