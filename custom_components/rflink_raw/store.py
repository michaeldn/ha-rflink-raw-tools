"""Persistent state store for RFLink Raw Tools."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import (
    DATA_STATE,
    DATA_STORE,
    DOMAIN,
    KEY_DASHBOARD_ENABLED,
    KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    KEY_DELAY_MS,
    KEY_LAST_UPDATE_BACKUP,
    KEY_PREREQ_INSTALLED,
    KEY_PREREQ_PORT,
    KEY_PREREQ_RECONNECT_INTERVAL,
    KEY_PREREQ_WAIT_FOR_ACK,
    KEY_PROTOCOL_COMMAND,
    KEY_PROTOCOL_DEVICE_ID,
    KEY_RAW_COMMAND,
    KEY_REPEAT,
    SIGNAL_STATE_UPDATED,
    STORAGE_KEY,
    STORAGE_VERSION,
)

DEFAULT_STATE = {
    KEY_PREREQ_PORT: "/dev/ttyUSB0",
    KEY_PREREQ_WAIT_FOR_ACK: False,
    KEY_PREREQ_RECONNECT_INTERVAL: 10,
    KEY_PREREQ_INSTALLED: False,
    KEY_DASHBOARD_ENABLED: False,
    KEY_DASHBOARD_SHOW_IN_SIDEBAR: False,
    KEY_RAW_COMMAND: "10;PING;",
    KEY_PROTOCOL_DEVICE_ID: "",
    KEY_PROTOCOL_COMMAND: "on",
    KEY_REPEAT: 1,
    KEY_DELAY_MS: 250,
    KEY_LAST_UPDATE_BACKUP: "",
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
    """Return current state."""
    return hass.data.setdefault(DOMAIN, {}).setdefault(DATA_STATE, DEFAULT_STATE.copy())


@callback
def update_state(hass: HomeAssistant, **changes) -> None:
    """Update state, persist it, and refresh entities."""
    state = get_state(hass)
    state.update(changes)
    store = hass.data.get(DOMAIN, {}).get(DATA_STORE)
    if store is not None:
        hass.async_create_task(store.async_save(dict(state)))
    async_dispatcher_send(hass, SIGNAL_STATE_UPDATED)
