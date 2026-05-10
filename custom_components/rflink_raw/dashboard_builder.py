"""Dynamic dashboard builder for RFLink Raw Tools."""

from __future__ import annotations

from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DASHBOARD_FILENAME


ENTITY_SUFFIXES = {
    "prereq_port": "text.rflink_prerequisite_port",
    "prereq_reconnect_interval": "number.rflink_prerequisite_reconnect_interval",
    "prereq_wait_for_ack": "switch.rflink_prerequisite_wait_for_ack",
    "managed_prerequisite": "switch.rflink_prerequisite",
    "managed_dashboard": "switch.rflink_dashboard",
    "managed_sidebar": "switch.rflink_sidebar",

    "raw_command": "text.rflink_raw_command",
    "protocol_device_id": "text.rflink_protocol_device_id",
    "protocol_command": "text.rflink_protocol_command",
    "repeat_count": "number.rflink_repeat_count",
    "repeat_delay": "number.rflink_repeat_delay",
    "qrfdebug": "switch.rflink_qrfdebug",
    "rfdebug": "switch.rflink_rfdebug",

    # Optional/advanced current entities. These may be disabled or absent.
    "send_raw_command": "switch.send_rflink_raw_command",
    "send_protocol_command": "switch.send_rflink_protocol_command",
    "ping": "switch.rflink_ping",
    "version": "switch.rflink_version",
    "update_from_github": "switch.update_download_latest_from_github",
    "restore_last_update": "switch.undo_last_github_update",
}

REQUIRED_SUFFIXES = {
    "managed_prerequisite",
    "managed_dashboard",
    "managed_sidebar",
    "prereq_reconnect_interval",
    "prereq_wait_for_ack",
    "raw_command",
    "protocol_command",
    "repeat_count",
    "repeat_delay",
    "qrfdebug",
    "rfdebug",
}


def _entity_map(hass: HomeAssistant) -> dict[str, str]:
    """Return current entity IDs keyed by RFLink Raw Tools unique-id suffix."""
    registry = er.async_get(hass)
    found: dict[str, str] = {}

    for entity_entry in registry.entities.values():
        if entity_entry.platform != "rflink_raw":
            continue

        unique_id = entity_entry.unique_id or ""
        entity_id = entity_entry.entity_id

        for suffix, fallback in ENTITY_SUFFIXES.items():
            if unique_id.endswith(f"_{suffix}"):
                found[suffix] = entity_id
                break

        for suffix, fallback in ENTITY_SUFFIXES.items():
            if entity_id == fallback:
                found.setdefault(suffix, entity_id)

    return found


def _entity_line(entity_id: str, name: str) -> str:
    return f"              - entity: {entity_id}\n                name: {name}\n"


def _button_card(name: str, icon: str, service: str) -> str:
    return (
        "              - type: button\n"
        f"                name: {name}\n"
        f"                icon: {icon}\n"
        "                tap_action:\n"
        "                  action: call-service\n"
        f"                  service: {service}\n"
    )


def build_dashboard_yaml(hass: HomeAssistant) -> str:
    """Build Lovelace YAML using actual entity IDs assigned by Home Assistant."""
    e = _entity_map(hass)
    missing_required = sorted(suffix for suffix in REQUIRED_SUFFIXES if suffix not in e)

    prereq_rows = ""
    for suffix, label in [
        ("prereq_port", "Port"),
        ("prereq_reconnect_interval", "Reconnect interval"),
        ("prereq_wait_for_ack", "Wait for ACK"),
        ("managed_prerequisite", "Install RFLink"),
    ]:
        if suffix in e:
            prereq_rows += _entity_line(e[suffix], label)

    dashboard_rows = ""
    for suffix, label in [
        ("managed_dashboard", "Dashboard"),
        ("managed_sidebar", "Sidebar"),
    ]:
        if suffix in e:
            dashboard_rows += _entity_line(e[suffix], label)

    command_rows = ""
    for suffix, label in [
        ("raw_command", "Raw command"),
        ("protocol_device_id", "Protocol device ID"),
        ("protocol_command", "Protocol command"),
        ("repeat_count", "Repeat"),
        ("repeat_delay", "Delay"),
    ]:
        if suffix in e:
            command_rows += _entity_line(e[suffix], label)

    capture_rows = ""
    for suffix, label in [
        ("qrfdebug", "QRFDEBUG"),
        ("rfdebug", "RFDEBUG"),
    ]:
        if suffix in e:
            capture_rows += _entity_line(e[suffix], label)

    missing_block = ""
    if missing_required:
        missing_list = "\n".join(f"              - `{item}`" for item in missing_required)
        missing_block = (
            "          - type: markdown\n"
            "            content: |\n"
            "              ### Missing required entities\n\n"
            "              The dashboard rebuilt, but these required RFLink Raw Tools entities were not in the registry yet:\n\n"
            f"{missing_list}\n\n"
            "              Run **Developer Tools → Actions → rflink_raw.reset_ui**, restart Home Assistant Core, then run **rflink_raw.rebuild_dashboard**.\n\n"
        )

    return f"""title: RFLink Raw Tools
views:
  - title: Start
    path: rflink-start
    icon: mdi:home-automation
    cards:
      - type: markdown
        content: |
          <p align="center"><img src="/local/rflink_raw/logo.png" width="96"></p>

          # RFLink Raw Tools

          Setup uses on/off switches. This dashboard is generated from the actual Home Assistant entity registry.

      - type: grid
        columns: 2
        square: false
        cards:
          - type: button
            name: Setup
            icon: mdi:cog-outline
            tap_action:
              action: navigate
              navigation_path: /rflink-raw-tools/rflink-setup
          - type: button
            name: Control
            icon: mdi:remote
            tap_action:
              action: navigate
              navigation_path: /rflink-raw-tools/rflink-control
          - type: button
            name: Debug
            icon: mdi:radio-tower
            tap_action:
              action: navigate
              navigation_path: /rflink-raw-tools/rflink-debug
          - type: button
            name: Update
            icon: mdi:update
            tap_action:
              action: navigate
              navigation_path: /rflink-raw-tools/rflink-update
{missing_block}
  - title: Setup
    path: rflink-setup
    icon: mdi:cog-outline
    cards:
      - type: markdown
        content: |
          ## Setup

          Turn a switch on to apply. Turn it off to undo.

      - type: entities
        title: Install RFLink
        show_header_toggle: false
        entities:
{prereq_rows if prereq_rows else '          - type: section\n            label: No prerequisite entities found yet\n'}
      - type: entities
        title: Dashboard
        show_header_toggle: false
        entities:
{dashboard_rows if dashboard_rows else '          - type: section\n            label: No dashboard entities found yet\n'}
  - title: Control
    path: rflink-control
    icon: mdi:remote
    cards:
      - type: entities
        title: Command values
        show_header_toggle: false
        entities:
{command_rows if command_rows else '          - type: section\n            label: No command entities found yet\n'}
      - type: grid
        title: Send
        columns: 2
        square: false
        cards:
{_button_card('Send raw', 'mdi:send', 'rflink_raw.send_stored_raw')}{_button_card('Send protocol', 'mdi:remote', 'rflink_raw.send_stored_protocol')}
  - title: Debug
    path: rflink-debug
    icon: mdi:radio-tower
    cards:
      - type: entities
        title: Capture
        show_header_toggle: false
        entities:
{capture_rows if capture_rows else '          - type: section\n            label: No debug entities found yet\n'}
      - type: grid
        title: One-time commands
        columns: 2
        square: false
        cards:
{_button_card('Ping', 'mdi:access-point-check', 'rflink_raw.ping_gateway')}{_button_card('Version', 'mdi:information-outline', 'rflink_raw.version_gateway')}
  - title: Update
    path: rflink-update
    icon: mdi:update
    cards:
      - type: markdown
        content: |
          ## Update and reset

          Use **Reset UI** after updates if controls look stale or duplicated.

      - type: grid
        columns: 2
        square: false
        cards:
{_button_card('Download latest', 'mdi:cloud-download-outline', 'rflink_raw.update_from_github')}{_button_card('Undo update', 'mdi:backup-restore', 'rflink_raw.restore_last_update')}{_button_card('Reset UI', 'mdi:broom', 'rflink_raw.reset_ui')}{_button_card('Rebuild dashboard', 'mdi:view-dashboard-edit', 'rflink_raw.rebuild_dashboard')}
"""


async def async_write_dashboard_file(hass: HomeAssistant) -> None:
    """Write dashboard YAML using current entity IDs."""
    dashboard_path = Path(hass.config.path(DASHBOARD_FILENAME))
    dashboard_path.write_text(build_dashboard_yaml(hass))
