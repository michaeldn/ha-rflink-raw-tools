"""Sensor platform for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import (
    DEVICE_IDENTIFIER,
    DEVICE_NAME,
    DOMAIN,
    KEY_LAST_COMMAND,
    KEY_LAST_ERROR,
    KEY_LAST_RESPONSE,
    KEY_PREREQ_STATUS,
    MANUFACTURER,
    MODEL,
    VERSION,
)
from .store import get_state


@dataclass(frozen=True, kw_only=True)
class RFLinkRawSensorDescription(EntityDescription):
    """Description for an RFLink Raw Tools sensor."""

    state_key: str


SENSORS: tuple[RFLinkRawSensorDescription, ...] = (
    RFLinkRawSensorDescription(key="prereq_status", name="RFLink Prerequisite Status", icon="mdi:file-check-outline", state_key=KEY_PREREQ_STATUS),
    RFLinkRawSensorDescription(key="last_command", name="RFLink Last Command", icon="mdi:history", state_key=KEY_LAST_COMMAND),
    RFLinkRawSensorDescription(key="last_response", name="RFLink Last Response", icon="mdi:message-reply-text", state_key=KEY_LAST_RESPONSE),
    RFLinkRawSensorDescription(key="last_error", name="RFLink Last Error", icon="mdi:alert-circle-outline", state_key=KEY_LAST_ERROR),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up RFLink Raw Tools sensors."""
    async_add_entities(RFLinkRawSensor(hass, entry.entry_id, description) for description in SENSORS)


class RFLinkRawSensor(SensorEntity):
    """RFLink Raw Tools sensor."""

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawSensorDescription) -> None:
        """Initialize the sensor."""
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

    @property
    def native_value(self) -> str:
        """Return sensor value."""
        value = get_state(self.hass).get(self.entity_description.state_key, "")
        if len(value) > 250:
            return value[:247] + "..."
        return value
