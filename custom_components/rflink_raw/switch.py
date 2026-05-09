"""Switch entities for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityDescription

from .const import (
    ADMIN_DEVICE_IDENTIFIER,
    ADMIN_DEVICE_NAME,
    COMMAND_DEVICE_IDENTIFIER,
    COMMAND_DEVICE_NAME,
    DOMAIN,
    KEY_PREREQ_WAIT_FOR_ACK,
    MANUFACTURER,
    MODEL,
    SIGNAL_STATE_UPDATED,
    VERSION,
)
from .helpers import async_send_direct_command
from .store import get_state, update_state


@dataclass(frozen=True, kw_only=True)
class RFLinkRawSwitchDescription(EntityDescription):
    """Switch description."""

    switch_type: str
    state_key: str | None = None
    on_command: str | None = None
    off_command: str | None = None
    device_area: str = "command"


SWITCHES = (
    RFLinkRawSwitchDescription(
        key="prereq_wait_for_ack",
        name="RFLink Prerequisite Wait For ACK",
        icon="mdi:handshake-outline",
        switch_type="state",
        state_key=KEY_PREREQ_WAIT_FOR_ACK,
        device_area="admin",
    ),
    RFLinkRawSwitchDescription(
        key="qrfdebug",
        name="RFLink QRFDEBUG",
        icon="mdi:signal",
        switch_type="command",
        on_command="10;QRFDEBUG=ON;",
        off_command="10;QRFDEBUG=OFF;",
        device_area="command",
    ),
    RFLinkRawSwitchDescription(
        key="rfdebug",
        name="RFLink RFDEBUG",
        icon="mdi:radio-tower",
        switch_type="command",
        on_command="10;RFDEBUG=ON;",
        off_command="10;RFDEBUG=OFF;",
        device_area="command",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up switch entities."""
    async_add_entities(RFLinkRawSwitch(hass, entry.entry_id, desc) for desc in SWITCHES)


class RFLinkRawSwitch(SwitchEntity):
    """RFLink switch."""

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawSwitchDescription) -> None:
        self.hass = hass
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._command_is_on = False

        if description.device_area == "admin":
            identifier = ADMIN_DEVICE_IDENTIFIER
            name = ADMIN_DEVICE_NAME
        else:
            identifier = COMMAND_DEVICE_IDENTIFIER
            name = COMMAND_DEVICE_NAME

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
        )

    async def async_added_to_hass(self) -> None:
        """Refresh state when state changes."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_STATE_UPDATED, self.async_write_ha_state)
        )

    @property
    def is_on(self) -> bool:
        """Return state."""
        if self.entity_description.switch_type == "state":
            return bool(get_state(self.hass).get(self.entity_description.state_key, False))
        return bool(self._command_is_on)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on."""
        if self.entity_description.switch_type == "state":
            update_state(self.hass, **{self.entity_description.state_key: True})
        else:
            await async_send_direct_command(self.hass, self.entity_description.on_command, 1, 250)
            self._command_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off."""
        if self.entity_description.switch_type == "state":
            update_state(self.hass, **{self.entity_description.state_key: False})
        else:
            await async_send_direct_command(self.hass, self.entity_description.off_command, 1, 250)
            self._command_is_on = False
            self.async_write_ha_state()
