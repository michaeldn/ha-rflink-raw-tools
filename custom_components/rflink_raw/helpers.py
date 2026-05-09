"""Helpers for RFLink Raw Tools."""

from __future__ import annotations

import asyncio
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


def normalize_repeat(repeat: int | float | str | None) -> int:
    """Normalize repeat count."""
    try:
        value = int(float(repeat if repeat is not None else 1))
    except (TypeError, ValueError) as err:
        raise HomeAssistantError("repeat must be a number.") from err

    if value < 1:
        raise HomeAssistantError("repeat must be 1 or greater.")

    if value > 50:
        raise HomeAssistantError("repeat is capped at 50 for safety.")

    return value


def normalize_delay_ms(delay_ms: int | float | str | None) -> int:
    """Normalize repeat delay in milliseconds."""
    try:
        value = int(float(delay_ms if delay_ms is not None else 250))
    except (TypeError, ValueError) as err:
        raise HomeAssistantError("delay_ms must be a number.") from err

    if value < 0:
        raise HomeAssistantError("delay_ms cannot be negative.")

    if value > 10000:
        raise HomeAssistantError("delay_ms is capped at 10000 for safety.")

    return value


async def async_send_direct_command(
    hass: HomeAssistant,
    raw_command: str,
    repeat: int | float | str | None = 1,
    delay_ms: int | float | str | None = 250,
) -> None:
    """Send one direct RFLink serial command line, optionally repeated."""
    try:
        command = normalize_raw_command(raw_command)
        repeat_count = normalize_repeat(repeat)
        delay_value_ms = normalize_delay_ms(delay_ms)
        protocol = get_rflink_protocol()

        _LOGGER.warning(
            "Sending direct RFLink command line: %s repeat=%s delay_ms=%s",
            command,
            repeat_count,
            delay_value_ms,
        )

        for index in range(repeat_count):
            protocol.send_raw_packet(command)
            if index < repeat_count - 1 and delay_value_ms:
                await asyncio.sleep(delay_value_ms / 1000)

        update_state(
            hass,
            **{
                KEY_LAST_COMMAND: timestamped(
                    f"{command} repeat={repeat_count} delay_ms={delay_value_ms}"
                ),
                KEY_LAST_RESPONSE: "Command written to RFLink serial connection",
                KEY_LAST_ERROR: "",
            },
        )
    except Exception as err:
        update_state(hass, **{KEY_LAST_ERROR: timestamped(str(err))})
        raise


async def async_send_protocol_command(
    hass: HomeAssistant,
    device_id: str,
    command: str,
    repeat: int | float | str | None = 1,
    delay_ms: int | float | str | None = 250,
) -> bool | None:
    """Send a normal RFLink protocol/device command, optionally repeated."""
    if not device_id.strip():
        raise HomeAssistantError("protocol device_id cannot be empty.")

    if not command.strip():
        raise HomeAssistantError("protocol command cannot be empty.")

    if not RflinkCommand.is_connected():
        raise HomeAssistantError("RFLink is not connected.")

    repeat_count = normalize_repeat(repeat)
    delay_value_ms = normalize_delay_ms(delay_ms)
    last_result = None

    _LOGGER.info(
        "Sending RFLink protocol command: %s -> %s repeat=%s delay_ms=%s",
        device_id,
        command,
        repeat_count,
        delay_value_ms,
    )

    for index in range(repeat_count):
        last_result = await RflinkCommand.send_command(device_id.strip(), command.strip())
        if index < repeat_count - 1 and delay_value_ms:
            await asyncio.sleep(delay_value_ms / 1000)

    update_state(
        hass,
        **{
            KEY_LAST_COMMAND: timestamped(
                f"{device_id.strip()} -> {command.strip()} "
                f"repeat={repeat_count} delay_ms={delay_value_ms}"
            ),
            KEY_LAST_RESPONSE: f"RFLink protocol command returned: {last_result}",
            KEY_LAST_ERROR: "",
        },
    )

    return last_result
