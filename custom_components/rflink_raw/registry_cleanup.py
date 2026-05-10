"""Registry cleanup helpers for RFLink Raw Tools."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)

CURRENT_ENTITY_IDS = {
    "switch.rflink_prerequisite",
    "switch.rflink_dashboard",
    "switch.rflink_sidebar",
    "switch.rflink_prerequisite_wait_for_ack",
    "text.rflink_prerequisite_port",
    "number.rflink_prerequisite_reconnect_interval",
    "switch.send_rflink_raw_command",
    "switch.send_rflink_protocol_command",
    "switch.rflink_qrfdebug",
    "switch.rflink_rfdebug",
    "switch.rflink_ping",
    "switch.rflink_version",
    "text.rflink_raw_command",
    "text.rflink_protocol_device_id",
    "text.rflink_protocol_command",
    "number.rflink_repeat_count",
    "number.rflink_repeat_delay",
    "switch.update_download_latest_from_github",
    "switch.undo_last_github_update",
}


def _is_stale_rflink_raw_entity(entity_entry: er.RegistryEntry) -> bool:
    """Return true if a registry entity is from an old RFLink Raw Tools build."""
    if entity_entry.platform != "rflink_raw":
        return False

    entity_id = entity_entry.entity_id

    # Current build intentionally has no ButtonEntity platform.
    if entity_id.startswith("button."):
        return True

    stale_prefixes = (
        "switch.add_dashboard",
        "switch.add_to_sidebar",
        "switch.dashboard_",
        "switch.install_rflink_prerequisite",
        "switch.setup_",
        "switch.control_",
        "switch.debug_",
        "text.control_",
        "text.setup_",
        "number.control_",
        "number.setup_",
        "sensor.",
    )
    if entity_id.startswith(stale_prefixes):
        return True

    return entity_id not in CURRENT_ENTITY_IDS


async def async_reset_ui_registry(hass: HomeAssistant) -> list[str]:
    """Remove stale RFLink Raw Tools registry entities and old orphan devices."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    removed_entities: list[str] = []

    for entity_entry in list(entity_registry.entities.values()):
        if _is_stale_rflink_raw_entity(entity_entry):
            removed_entities.append(entity_entry.entity_id)
            entity_registry.async_remove(entity_entry.entity_id)

    current_identifiers = {
        ("rflink_raw", "rflink_raw_tools_admin"),
        ("rflink_raw", "rflink_raw_tools_command_center"),
    }
    entity_device_ids = {
        entry.device_id
        for entry in entity_registry.entities.values()
        if entry.platform == "rflink_raw" and entry.device_id
    }

    for device_entry in list(device_registry.devices.values()):
        identifiers = set(device_entry.identifiers)
        if not any(identifier[0] == "rflink_raw" for identifier in identifiers):
            continue
        if identifiers.intersection(current_identifiers):
            continue
        if device_entry.id in entity_device_ids:
            continue
        device_registry.async_remove_device(device_entry.id)

    if removed_entities:
        _LOGGER.warning(
            "RFLink Raw Tools removed stale registry entities: %s",
            ", ".join(removed_entities),
        )

    return removed_entities
