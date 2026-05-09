"""Helpers for RFLink Raw Tools."""

from __future__ import annotations

import logging

from homeassistant.components.rflink.entity import RflinkCommand
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import KEY_LAST_COMMAND, KEY_LAST_ERROR, KEY_LAST_RESPONSE
from .store import timestamped, update_state

_LOGGER = logging.getLogger(__name__)


def get_rflink_protocol():
    """Return the currently connected RFLink protocol from Home Assistant."""
    protocol = getattr(RflinkCommand, "_protocol", None)

    if protocol is None:
        raise HomeAssistantError(
            "RFLink is not connected. Confirm the core RFLink integration is configured "
            "and shows 'Connected to Rflink' in the logs."
        )

    if not hasattr(protocol, "send_raw_packet"):
        raise HomeAssistantError(
            "The loaded RFLink protocol object does not expose send_raw_packet()."
        )

    return protocol


def normalize_raw_command(raw_command: str) -> str:
    """Normalize and validate one direct RFLink command line."""
    command = raw_command.strip().replace("\r", "").replace("\n", "")

    if not command:
        raise HomeAssistantError("raw_command cannot be empty.")

    if not command.startswith("10;"):
        raise HomeAssistantError(
            "For safety, raw_command must start with '10;'. "
            "Example: 10;RFDEBUG=ON;"
        )

    if not command.endswith(";"):
        command += ";"

    return command


def send_direct_command(hass: HomeAssistant, raw_command: str) -> None:
    """Send one direct RFLink serial command line."""
    try:
        command = normalize_raw_command(raw_command)
        protocol = get_rflink_protocol()

        _LOGGER.warning("Sending direct RFLink command line: %s", command)
        protocol.send_raw_packet(command)

        update_state(
            hass,
            **{
                KEY_LAST_COMMAND: timestamped(command),
                KEY_LAST_RESPONSE: "Command written to RFLink serial connection",
                KEY_LAST_ERROR: "",
            },
        )
    except Exception as err:
        update_state(hass, **{KEY_LAST_ERROR: timestamped(str(err))})
        raise


async def send_protocol_command(
    hass: HomeAssistant, device_id: str, command: str
) -> bool | None:
    """Send a normal RFLink protocol/device command."""
    if not device_id.strip():
        raise HomeAssistantError("protocol device_id cannot be empty.")

    if not command.strip():
        raise HomeAssistantError("protocol command cannot be empty.")

    if not RflinkCommand.is_connected():
        raise HomeAssistantError("RFLink is not connected.")

    _LOGGER.info("Sending RFLink protocol command: %s -> %s", device_id, command)
    ok = await RflinkCommand.send_command(device_id.strip(), command.strip())

    update_state(
        hass,
        **{
            KEY_LAST_COMMAND: timestamped(f"{device_id.strip()} -> {command.strip()}"),
            KEY_LAST_RESPONSE: f"RFLink protocol command returned: {ok}",
            KEY_LAST_ERROR: "",
        },
    )

    return ok
