"""Button platform for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import (
    DEVICE_IDENTIFIER,
    DEVICE_NAME,
    DOMAIN,
    KEY_DELAY_MS,
    KEY_PROTOCOL_COMMAND,
    KEY_PROTOCOL_DEVICE_ID,
    KEY_RAW_COMMAND,
    KEY_REPEAT,
    MANUFACTURER,
    MODEL,
    VERSION,
)
from .helpers import async_send_direct_command, async_send_protocol_command
from .store import get_state


@dataclass(frozen=True, kw_only=True)
class RFLinkRawButtonDescription(EntityDescription):
    """Description for an RFLink raw command button."""

    command: str | None = None
    action_type: str = "direct"


BUTTONS: tuple[RFLinkRawButtonDescription, ...] = (
    RFLinkRawButtonDescription(
        key="send_raw_text",
        name="Send RFLink Raw Command",
        icon="mdi:send",
        action_type="send_raw_text",
    ),
    RFLinkRawButtonDescription(
        key="send_protocol_text",
        name="Send RFLink Protocol Command",
        icon="mdi:remote",
        action_type="send_protocol_text",
    ),
    RFLinkRawButtonDescription(key="ping", name="RFLink Ping", icon="mdi:access-point-check", command="10;PING;"),
    RFLinkRawButtonDescription(key="version", name="RFLink Version", icon="mdi:information-outline", command="10;VERSION;"),
    RFLinkRawButtonDescription(key="status", name="RFLink Status", icon="mdi:list-status", command="10;STATUS;"),
    RFLinkRawButtonDescription(key="rfdebug_on", name="Start RFDEBUG Capture", icon="mdi:radio-tower", command="10;RFDEBUG=ON;"),
    RFLinkRawButtonDescription(key="rfdebug_off", name="Stop RFDEBUG Capture", icon="mdi:radio-tower", command="10;RFDEBUG=OFF;"),
    RFLinkRawButtonDescription(key="qrfdebug_on", name="Start QRFDEBUG Capture", icon="mdi:signal", command="10;QRFDEBUG=ON;"),
    RFLinkRawButtonDescription(key="qrfdebug_off", name="Stop QRFDEBUG Capture", icon="mdi:signal-off", command="10;QRFDEBUG=OFF;"),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up RFLink Raw Tools buttons."""
    async_add_entities(RFLinkRawButton(hass, entry.entry_id, description) for description in BUTTONS)


class RFLinkRawButton(ButtonEntity):
    """RFLink command button."""

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawButtonDescription) -> None:
        """Initialize the button."""
        self.hass = hass
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DEVICE_IDENTIFIER)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
        )

    async def async_press(self) -> None:
        """Send the RFLink command."""
        state = get_state(self.hass)

        if self.entity_description.action_type == "send_raw_text":
            await async_send_direct_command(
                self.hass,
                state[KEY_RAW_COMMAND],
                state[KEY_REPEAT],
                state[KEY_DELAY_MS],
            )
            return

        if self.entity_description.action_type == "send_protocol_text":
            await async_send_protocol_command(
                self.hass,
                state[KEY_PROTOCOL_DEVICE_ID],
                state[KEY_PROTOCOL_COMMAND],
                state[KEY_REPEAT],
                state[KEY_DELAY_MS],
            )
            return

        await async_send_direct_command(self.hass, self.entity_description.command, 1, 250)
