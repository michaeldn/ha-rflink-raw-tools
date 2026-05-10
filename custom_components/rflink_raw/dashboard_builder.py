"""Dynamic dashboard builder for RFLink Raw Tools."""
from __future__ import annotations
from pathlib import Path
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from .const import DASHBOARD_FILENAME

ENTITY_SUFFIXES = {
    "prereq_port":"text.rflink_prerequisite_port",
    "prereq_reconnect_interval":"number.rflink_prerequisite_reconnect_interval",
    "prereq_wait_for_ack":"switch.rflink_prerequisite_wait_for_ack",
    "managed_prerequisite":"switch.rflink_prerequisite",
    "managed_dashboard":"switch.rflink_dashboard",
    "managed_sidebar":"switch.rflink_sidebar",
    "raw_command":"text.rflink_raw_command",
    "protocol_device_id":"text.rflink_protocol_device_id",
    "protocol_command":"text.rflink_protocol_command",
    "repeat_count":"number.rflink_repeat_count",
    "repeat_delay":"number.rflink_repeat_delay",
    "send_raw_command":"switch.send_rflink_raw_command",
    "send_protocol_command":"switch.send_rflink_protocol_command",
    "qrfdebug":"switch.rflink_qrfdebug",
    "rfdebug":"switch.rflink_rfdebug",
    "ping":"switch.rflink_ping",
    "version":"switch.rflink_version",
    "update_from_github":"switch.update_download_latest_from_github",
    "restore_last_update":"switch.undo_last_github_update",
}

def _entity_map(hass: HomeAssistant) -> dict[str, str]:
    registry = er.async_get(hass)
    found: dict[str, str] = {}
    for entity_entry in registry.entities.values():
        if entity_entry.platform != "rflink_raw":
            continue
        unique_id = entity_entry.unique_id or ""
        entity_id = entity_entry.entity_id
        for suffix, fallback in ENTITY_SUFFIXES.items():
            if unique_id.endswith(f"_{suffix}") or entity_id == fallback:
                found.setdefault(suffix, entity_id)
                break
    return found

def _entity_line(entity_id: str, name: str) -> str:
    return f"              - entity: {entity_id}\n                name: {name}\n"

def _button_card(name: str, icon: str, service: str) -> str:
    return ("              - type: button\n"
            f"                name: {name}\n"
            f"                icon: {icon}\n"
            "                tap_action:\n"
            "                  action: call-service\n"
            f"                  service: {service}\n")

def _rows(e: dict[str,str], items: list[tuple[str,str]], fallback: str) -> str:
    rows = ""
    for suffix, label in items:
        if suffix in e:
            rows += _entity_line(e[suffix], label)
    return rows or f"              - type: section\n                label: {fallback}\n"

def build_dashboard_yaml(hass: HomeAssistant) -> str:
    e = _entity_map(hass)
    missing = [suffix for suffix in ENTITY_SUFFIXES if suffix not in e]
    missing_block = ""
    if missing:
        missing_list = "\n".join(f"              - `{item}`" for item in missing)
        missing_block = f"""      - type: markdown
        content: |
          ### Missing entities

          The dashboard rebuilt, but these expected RFLink Raw Tools entities were not in the registry yet:

{missing_list}

          Run **Developer Tools → Actions → rflink_raw.reset_ui**, then restart Home Assistant Core.
"""
    prereq = _rows(e, [("prereq_port","Port"),("prereq_reconnect_interval","Reconnect interval"),("prereq_wait_for_ack","Wait for ACK"),("managed_prerequisite","RFLink prerequisite")], "No prerequisite entities found yet")
    dash = _rows(e, [("managed_dashboard","Dashboard"),("managed_sidebar","Sidebar")], "No dashboard entities found yet")
    command = _rows(e, [("raw_command","Raw command"),("protocol_device_id","Protocol device ID"),("protocol_command","Protocol command"),("repeat_count","Repeat"),("repeat_delay","Delay")], "No command entities found yet")
    debug = _rows(e, [("qrfdebug","QRFDEBUG"),("rfdebug","RFDEBUG")], "No debug entities found yet")
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
        title: RFLink prerequisite
        show_header_toggle: false
        entities:
{prereq}      - type: entities
        title: Dashboard
        show_header_toggle: false
        entities:
{dash}  - title: Control
    path: rflink-control
    icon: mdi:remote
    cards:
      - type: entities
        title: Command values
        show_header_toggle: false
        entities:
{command}      - type: grid
        title: Send
        columns: 2
        square: false
        cards:
{_button_card('Send raw','mdi:send','rflink_raw.send_stored_raw')}{_button_card('Send protocol','mdi:remote','rflink_raw.send_stored_protocol')}  - title: Debug
    path: rflink-debug
    icon: mdi:radio-tower
    cards:
      - type: entities
        title: Capture
        show_header_toggle: false
        entities:
{debug}      - type: grid
        title: One-time commands
        columns: 2
        square: false
        cards:
{_button_card('Ping','mdi:access-point-check','rflink_raw.ping')}{_button_card('Version','mdi:information-outline','rflink_raw.version')}  - title: Update
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
{_button_card('Download latest','mdi:cloud-download-outline','rflink_raw.update_from_github')}{_button_card('Undo update','mdi:backup-restore','rflink_raw.restore_last_update')}{_button_card('Reset UI','mdi:broom','rflink_raw.reset_ui')}{_button_card('Rebuild dashboard','mdi:view-dashboard-edit','rflink_raw.rebuild_dashboard')}"""

async def async_write_dashboard_file(hass: HomeAssistant) -> None:
    Path(hass.config.path(DASHBOARD_FILENAME)).write_text(build_dashboard_yaml(hass))
