"""Switch platform for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import DEVICE_IDENTIFIER, DEVICE_NAME, DOMAIN, MANUFACTURER, MODEL, VERSION
from .helpers import async_send_direct_command


@dataclass(frozen=True, kw_only=True)
class RFLinkRawSwitchDescription(EntityDescription):
    """Description for an RFLink raw command switch."""

    on_command: str
    off_command: str


SWITCHES: tuple[RFLinkRawSwitchDescription, ...] = (
    RFLinkRawSwitchDescription(
        key="rfdebug",
        name="RFLink RFDEBUG",
        icon="mdi:radio-tower",
        on_command="10;RFDEBUG=ON;",
        off_command="10;RFDEBUG=OFF;",
    ),
    RFLinkRawSwitchDescription(
        key="qrfdebug",
        name="RFLink QRFDEBUG",
        icon="mdi:signal",
        on_command="10;QRFDEBUG=ON;",
        off_command="10;QRFDEBUG=OFF;",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up RFLink Raw Tools switches."""
    async_add_entities(RFLinkRawSwitch(hass, entry.entry_id, description) for description in SWITCHES)


class RFLinkRawSwitch(SwitchEntity):
    """RFLink debug mode switch."""

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawSwitchDescription) -> None:
        """Initialize the switch."""
        self.hass = hass
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_is_on = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DEVICE_IDENTIFIER)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
        )

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on debug mode."""
        await async_send_direct_command(self.hass, self.entity_description.on_command, 1, 250)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off debug mode."""
        await async_send_direct_command(self.hass, self.entity_description.off_command, 1, 250)
        self._attr_is_on = False
        self.async_write_ha_state()
