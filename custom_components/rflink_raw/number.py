"""Number entities for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import (
    ADMIN_DEVICE_IDENTIFIER,
    ADMIN_DEVICE_NAME,
    COMMAND_DEVICE_IDENTIFIER,
    COMMAND_DEVICE_NAME,
    DOMAIN,
    KEY_DELAY_MS,
    KEY_PREREQ_RECONNECT_INTERVAL,
    KEY_REPEAT,
    MANUFACTURER,
    MODEL,
    VERSION,
)
from .store import get_state, update_state


@dataclass(frozen=True, kw_only=True)
class RFLinkRawNumberDescription(EntityDescription):
    """Number entity description."""

    state_key: str
    device_area: str
    native_min_value: float
    native_max_value: float
    native_step: float
    native_unit_of_measurement: str | None = None


NUMBERS: tuple[RFLinkRawNumberDescription, ...] = (
    RFLinkRawNumberDescription(
        key="prereq_reconnect_interval",
        name="RFLink Prerequisite Reconnect Interval",
        icon="mdi:connection",
        state_key=KEY_PREREQ_RECONNECT_INTERVAL,
        device_area="admin",
        native_min_value=1,
        native_max_value=3600,
        native_step=1,
        native_unit_of_measurement="s",
    ),
    RFLinkRawNumberDescription(
        key="repeat_count",
        name="RFLink Repeat Count",
        icon="mdi:repeat",
        state_key=KEY_REPEAT,
        device_area="command",
        native_min_value=1,
        native_max_value=50,
        native_step=1,
    ),
    RFLinkRawNumberDescription(
        key="repeat_delay",
        name="RFLink Repeat Delay",
        icon="mdi:timer-outline",
        state_key=KEY_DELAY_MS,
        device_area="command",
        native_min_value=0,
        native_max_value=10000,
        native_step=50,
        native_unit_of_measurement="ms",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up number entities."""
    async_add_entities(RFLinkRawNumber(hass, entry.entry_id, description) for description in NUMBERS)


class RFLinkRawNumber(NumberEntity):
    """RFLink Raw Tools number entity."""

    _attr_has_entity_name = False
    _attr_mode = NumberMode.BOX

    def __init__(self, hass, entry_id: str, description: RFLinkRawNumberDescription) -> None:
        self.hass = hass
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement

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

    @property
    def native_value(self) -> float:
        """Return current number value."""
        return float(get_state(self.hass).get(self.entity_description.state_key, 0))

    async def async_set_native_value(self, value: float) -> None:
        """Set number value."""
        update_state(self.hass, **{self.entity_description.state_key: int(value)})
        self.async_write_ha_state()
