"""Sensor entities for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory, EntityDescription

from .const import (
    ADMIN_DEVICE_IDENTIFIER,
    ADMIN_DEVICE_NAME,
    DOMAIN,
    KEY_LAST_UPDATE_FINISHED_AT,
    KEY_LAST_UPDATE_STARTED_AT,
    KEY_UPDATE_ERROR,
    KEY_UPDATE_MESSAGE,
    KEY_UPDATE_PROGRESS,
    KEY_UPDATE_STATUS,
    MANUFACTURER,
    MODEL,
    SIGNAL_STATE_UPDATED,
    VERSION,
)
from .store import get_state


@dataclass(frozen=True, kw_only=True)
class RFLinkRawSensorDescription(EntityDescription):
    """Sensor description."""

    state_key: str
    native_unit_of_measurement: str | None = None
    state_class: SensorStateClass | None = None


SENSORS: tuple[RFLinkRawSensorDescription, ...] = (
    RFLinkRawSensorDescription(
        key="update_status",
        name="RFLink Update Status",
        icon="mdi:progress-clock",
        state_key=KEY_UPDATE_STATUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RFLinkRawSensorDescription(
        key="update_progress",
        name="RFLink Update Progress",
        icon="mdi:progress-download",
        state_key=KEY_UPDATE_PROGRESS,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RFLinkRawSensorDescription(
        key="update_message",
        name="RFLink Update Message",
        icon="mdi:message-text-outline",
        state_key=KEY_UPDATE_MESSAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RFLinkRawSensorDescription(
        key="update_error",
        name="RFLink Update Error",
        icon="mdi:alert-circle-outline",
        state_key=KEY_UPDATE_ERROR,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RFLinkRawSensorDescription(
        key="last_update_started_at",
        name="RFLink Last Update Started",
        icon="mdi:clock-start",
        state_key=KEY_LAST_UPDATE_STARTED_AT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RFLinkRawSensorDescription(
        key="last_update_finished_at",
        name="RFLink Last Update Finished",
        icon="mdi:clock-check-outline",
        state_key=KEY_LAST_UPDATE_FINISHED_AT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up sensor entities."""
    async_add_entities(RFLinkRawSensor(hass, entry.entry_id, description) for description in SENSORS)


class RFLinkRawSensor(SensorEntity):
    """RFLink Raw Tools status sensor."""

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawSensorDescription) -> None:
        self.hass = hass
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_state_class = description.state_class
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ADMIN_DEVICE_IDENTIFIER)},
            name=ADMIN_DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
        )

    async def async_added_to_hass(self) -> None:
        """Refresh state when stored state changes."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_STATE_UPDATED, self.async_write_ha_state)
        )

    @property
    def native_value(self):
        """Return sensor value."""
        value = get_state(self.hass).get(self.entity_description.state_key, "")
        if self.entity_description.state_key == KEY_UPDATE_PROGRESS:
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0
        return value
