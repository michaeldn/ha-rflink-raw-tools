"""Persistent state store for RFLink Raw Tools."""

from __future__ import annotations

from datetime import datetime

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import (
    DATA_STATE,
    DATA_STORE,
    DOMAIN,
    KEY_DASHBOARD_REQUIRE_ADMIN,
    KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    KEY_DASHBOARD_STATUS,
    KEY_DELAY_MS,
    KEY_LAST_COMMAND,
    KEY_LAST_ERROR,
    KEY_LAST_RESPONSE,
    KEY_PREREQ_PORT,
    KEY_PREREQ_RECONNECT_INTERVAL,
    KEY_PREREQ_STATUS,
    KEY_PREREQ_WAIT_FOR_ACK,
    KEY_PROTOCOL_COMMAND,
    KEY_PROTOCOL_DEVICE_ID,
    KEY_RAW_COMMAND,
    KEY_REPEAT,
    KEY_UPDATE_STATUS,
    STORAGE_KEY,
    STORAGE_VERSION,
)

DEFAULT_STATE = {
    KEY_RAW_COMMAND: "10;PING;",
    KEY_PROTOCOL_DEVICE_ID: "",
    KEY_PROTOCOL_COMMAND: "on",
    KEY_REPEAT: 1,
    KEY_DELAY_MS: 250,
    KEY_PREREQ_PORT: "/dev/ttyUSB0",
    KEY_PREREQ_WAIT_FOR_ACK: False,
    KEY_PREREQ_RECONNECT_INTERVAL: 10,
    KEY_PREREQ_STATUS: "Not installed from RFLink Raw Tools",
    KEY_DASHBOARD_SHOW_IN_SIDEBAR: True,
    KEY_DASHBOARD_REQUIRE_ADMIN: False,
    KEY_DASHBOARD_STATUS: "Not installed from RFLink Raw Tools",
    KEY_UPDATE_STATUS: "Not updated from RFLink Raw Tools",
    KEY_LAST_COMMAND: "",
    KEY_LAST_RESPONSE: "",
    KEY_LAST_ERROR: "",
}


async def async_initialize_store(hass: HomeAssistant) -> None:
    """Initialize persistent storage."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    loaded = await store.async_load()
    state = DEFAULT_STATE.copy()
    if isinstance(loaded, dict):
        state.update(loaded)
    domain_data[DATA_STORE] = store
    domain_data[DATA_STATE] = state


@callback
def get_state(hass: HomeAssistant) -> dict:
    """Get integration state."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    return domain_data.setdefault(DATA_STATE, DEFAULT_STATE.copy())


@callback
def update_state(hass: HomeAssistant, **kwargs) -> None:
    """Update integration state and save it."""
    state = get_state(hass)
    state.update(kwargs)
    store = hass.data.get(DOMAIN, {}).get(DATA_STORE)
    if store is not None:
        hass.async_create_task(store.async_save(dict(state)))


def timestamped(value: str) -> str:
    """Return a timestamped state value."""
    return f"{datetime.now().isoformat(timespec='seconds')} — {value}"
