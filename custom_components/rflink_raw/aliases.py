"""Persistent RFLink Raw Tools aliases."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

SIGNAL_ALIASES_UPDATED = "rflink_raw_aliases_updated"
ALIASES_FILE = "rflink_raw_aliases.json"


def _path(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(ALIASES_FILE))


def _slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_]+", "_", (value or "").strip().lower()).strip("_")
    return clean or "rflink_alias"


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except Exception:
        return []
    if isinstance(data, dict):
        data = data.get("aliases", [])
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _write(path: Path, aliases: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps({"aliases": aliases}, indent=2, sort_keys=True) + "\n")


def normalize_alias(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get("name") or "").strip()
    device_id = str(data.get("device_id") or "").strip().lower()
    entity_type = str(data.get("entity_type") or "switch").strip().lower()

    if entity_type not in {"switch", "light", "button"}:
        entity_type = "switch"

    alias_id = str(data.get("id") or "").strip().lower()
    if not alias_id:
        alias_id = _slug(name or device_id)

    on_command = str(data.get("on_command") or "").strip()
    off_command = str(data.get("off_command") or "").strip()

    # Accept device_id + action fields by converting to the send_raw parser format.
    if not on_command and device_id:
        on_command = f"{device_id};on"
    if not off_command and device_id and entity_type in {"switch", "light"}:
        off_command = f"{device_id};off"

    return {
        "id": _slug(alias_id),
        "name": name or device_id or alias_id,
        "entity_type": entity_type,
        "device_id": device_id,
        "on_command": on_command,
        "off_command": off_command,
        "on_packet": str(data.get("on_packet") or "").strip(),
        "off_packet": str(data.get("off_packet") or "").strip(),
        "source_packet": str(data.get("source_packet") or "").strip(),
        "notes": str(data.get("notes") or "").strip(),
    }


async def async_list_aliases(hass: HomeAssistant) -> list[dict[str, Any]]:
    aliases = await hass.async_add_executor_job(_read, _path(hass))
    return [normalize_alias(alias) for alias in aliases]


async def async_save_alias(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    alias = normalize_alias(data)

    def _save() -> dict[str, Any]:
        path = _path(hass)
        aliases = [normalize_alias(item) for item in _read(path)]
        aliases = [item for item in aliases if item["id"] != alias["id"]]
        aliases.append(alias)
        aliases.sort(key=lambda item: item["name"].lower())
        _write(path, aliases)
        return alias

    return await hass.async_add_executor_job(_save)


async def async_delete_alias(hass: HomeAssistant, alias_id: str) -> list[dict[str, Any]]:
    clean_id = _slug(alias_id)

    def _delete() -> list[dict[str, Any]]:
        path = _path(hass)
        aliases = [normalize_alias(item) for item in _read(path)]
        aliases = [item for item in aliases if item["id"] != clean_id]
        _write(path, aliases)
        return aliases

    return await hass.async_add_executor_job(_delete)
