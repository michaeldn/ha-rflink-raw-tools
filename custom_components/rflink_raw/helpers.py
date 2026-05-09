"""Command helpers for RFLink Raw Tools."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_send_direct_command(
    hass: HomeAssistant,
    command: str,
    repeat: int = 1,
    delay_ms: int = 250,
) -> None:
    """Send a raw RFLink command through Home Assistant's RFLink gateway service."""
    clean = (command or "").strip()
    if not clean:
        raise ValueError("RFLink command cannot be empty.")

    repeat = max(1, int(repeat))
    delay_ms = max(0, int(delay_ms))

    for index in range(repeat):
        await hass.services.async_call(
            "rflink",
            "send_command",
            {"command": clean},
            blocking=True,
        )
        _LOGGER.info("Sent RFLink raw command %s/%s: %s", index + 1, repeat, clean)
        if index < repeat - 1 and delay_ms:
            await asyncio.sleep(delay_ms / 1000)


async def async_send_protocol_command(
    hass: HomeAssistant,
    device_id: str,
    command: str,
    repeat: int = 1,
    delay_ms: int = 250,
) -> None:
    """Send a protocol command using a RFLink device id."""
    clean_device = (device_id or "").strip()
    clean_command = (command or "").strip()
    if not clean_device:
        raise ValueError("RFLink protocol device id cannot be empty.")
    if not clean_command:
        raise ValueError("RFLink protocol command cannot be empty.")

    raw = f"10;{clean_device};{clean_command};"
    await async_send_direct_command(hass, raw, repeat, delay_ms)
