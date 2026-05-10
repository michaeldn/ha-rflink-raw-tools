"""RFLink Raw Tools integration."""

from __future__ import annotations

from datetime import datetime

import voluptuous as vol

from homeassistant.components import persistent_notification
from homeassistant.const import CONF_COMMAND, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    KEY_DASHBOARD_SHOW_IN_SIDEBAR,
    KEY_DELAY_MS,
    KEY_LAST_UPDATE_BACKUP,
    KEY_LAST_UPDATE_FINISHED_AT,
    KEY_LAST_UPDATE_STARTED_AT,
    KEY_PREREQ_PORT,
    KEY_PREREQ_RECONNECT_INTERVAL,
    KEY_PREREQ_WAIT_FOR_ACK,
    KEY_PROTOCOL_COMMAND,
    KEY_PROTOCOL_DEVICE_ID,
    KEY_RAW_COMMAND,
    KEY_REPEAT,
    KEY_UPDATE_ERROR,
    KEY_UPDATE_MESSAGE,
    KEY_UPDATE_PROGRESS,
    KEY_UPDATE_STATUS,
    PLATFORMS,
)
from .dashboard_builder import async_write_dashboard_file
from .helpers import async_send_direct_command, async_send_protocol_command
from .managed_config import (
    install_dashboard,
    install_prerequisite,
    remove_dashboard,
    remove_prerequisite,
    sync_prerequisite_state,
)
from .registry_cleanup import async_reset_ui_registry
from .store import async_initialize_store, get_state, update_state
from .updater import restore_last_update, update_from_github

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Any(None, vol.Schema({}))}, extra=vol.ALLOW_EXTRA)

SEND_RAW_SCHEMA = vol.Schema(
    {
        vol.Required("raw_command"): cv.string,
        vol.Optional("repeat", default=1): vol.Coerce(int),
        vol.Optional("delay_ms", default=250): vol.Coerce(int),
    }
)

SEND_PROTOCOL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_COMMAND): cv.string,
        vol.Optional("repeat", default=1): vol.Coerce(int),
        vol.Optional("delay_ms", default=250): vol.Coerce(int),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up RFLink Raw Tools services."""

    async def send_raw(call: ServiceCall) -> None:
        await async_send_direct_command(
            hass,
            call.data["raw_command"],
            call.data["repeat"],
            call.data["delay_ms"],
        )

    async def send_protocol(call: ServiceCall) -> None:
        await async_send_protocol_command(
            hass,
            call.data[CONF_DEVICE_ID],
            call.data[CONF_COMMAND],
            call.data["repeat"],
            call.data["delay_ms"],
        )

    async def send_stored_raw(call: ServiceCall) -> None:
        state = get_state(hass)
        await async_send_direct_command(
            hass,
            state[KEY_RAW_COMMAND],
            state[KEY_REPEAT],
            state[KEY_DELAY_MS],
        )

    async def send_stored_protocol(call: ServiceCall) -> None:
        state = get_state(hass)
        await async_send_protocol_command(
            hass,
            state[KEY_PROTOCOL_DEVICE_ID],
            state[KEY_PROTOCOL_COMMAND],
            state[KEY_REPEAT],
            state[KEY_DELAY_MS],
        )

    async def do_ping_gateway(call: ServiceCall) -> None:
        await async_send_direct_command(hass, "10;PING;", 1, 250)

    async def do_version_gateway(call: ServiceCall) -> None:
        await async_send_direct_command(hass, "10;VERSION;", 1, 250)

    async def do_update(call: ServiceCall) -> None:
        update_state(
            hass,
            **{
                KEY_UPDATE_STATUS: "starting",
                KEY_UPDATE_PROGRESS: 1,
                KEY_UPDATE_MESSAGE: "Starting RFLink Raw Tools update.",
                KEY_UPDATE_ERROR: "",
                KEY_LAST_UPDATE_STARTED_AT: datetime.now().isoformat(timespec="seconds"),
            },
        )

        def progress_callback(progress: int, status: str, message: str) -> None:
            update_state(
                hass,
                **{
                    KEY_UPDATE_STATUS: status,
                    KEY_UPDATE_PROGRESS: int(progress),
                    KEY_UPDATE_MESSAGE: message,
                    KEY_UPDATE_ERROR: "",
                },
            )

        try:
            backup_path = await hass.async_add_executor_job(
                update_from_github,
                hass,
                progress_callback,
            )
            update_state(
                hass,
                **{
                    KEY_LAST_UPDATE_BACKUP: backup_path,
                    KEY_UPDATE_STATUS: "complete",
                    KEY_UPDATE_PROGRESS: 100,
                    KEY_UPDATE_MESSAGE: "Update installed. Restart Home Assistant Core. If entities/devices still look wrong after reset/rebuild, delete and re-add the RFLink Raw Tools integration once.",
                    KEY_UPDATE_ERROR: "",
                    KEY_LAST_UPDATE_FINISHED_AT: datetime.now().isoformat(timespec="seconds"),
                },
            )
        except Exception as err:
            update_state(
                hass,
                **{
                    KEY_UPDATE_STATUS: "error",
                    KEY_UPDATE_PROGRESS: 0,
                    KEY_UPDATE_MESSAGE: "Update failed.",
                    KEY_UPDATE_ERROR: str(err),
                    KEY_LAST_UPDATE_FINISHED_AT: datetime.now().isoformat(timespec="seconds"),
                },
            )
            raise

    async def do_restore(call: ServiceCall) -> None:
        state = get_state(hass)
        backup_path = state.get(KEY_LAST_UPDATE_BACKUP, "")
        update_state(
            hass,
            **{
                KEY_UPDATE_STATUS: "restore_starting",
                KEY_UPDATE_PROGRESS: 1,
                KEY_UPDATE_MESSAGE: "Starting RFLink Raw Tools restore.",
                KEY_UPDATE_ERROR: "",
                KEY_LAST_UPDATE_STARTED_AT: datetime.now().isoformat(timespec="seconds"),
            },
        )

        def progress_callback(progress: int, status: str, message: str) -> None:
            update_state(
                hass,
                **{
                    KEY_UPDATE_STATUS: status,
                    KEY_UPDATE_PROGRESS: int(progress),
                    KEY_UPDATE_MESSAGE: message,
                    KEY_UPDATE_ERROR: "",
                },
            )

        try:
            restored_path = await hass.async_add_executor_job(
                restore_last_update,
                hass,
                backup_path,
                progress_callback,
            )
            update_state(
                hass,
                **{
                    KEY_LAST_UPDATE_BACKUP: restored_path,
                    KEY_UPDATE_STATUS: "restore_complete",
                    KEY_UPDATE_PROGRESS: 100,
                    KEY_UPDATE_MESSAGE: "Backup restored. Restart Home Assistant Core.",
                    KEY_UPDATE_ERROR: "",
                    KEY_LAST_UPDATE_FINISHED_AT: datetime.now().isoformat(timespec="seconds"),
                },
            )
        except Exception as err:
            update_state(
                hass,
                **{
                    KEY_UPDATE_STATUS: "restore_error",
                    KEY_UPDATE_PROGRESS: 0,
                    KEY_UPDATE_MESSAGE: "Restore failed.",
                    KEY_UPDATE_ERROR: str(err),
                    KEY_LAST_UPDATE_FINISHED_AT: datetime.now().isoformat(timespec="seconds"),
                },
            )
            raise

    async def do_install_prerequisite(call: ServiceCall) -> None:
        state = get_state(hass)
        install_prerequisite(
            hass,
            state[KEY_PREREQ_PORT],
            bool(state[KEY_PREREQ_WAIT_FOR_ACK]),
            int(state[KEY_PREREQ_RECONNECT_INTERVAL]),
        )

    async def do_remove_prerequisite(call: ServiceCall) -> None:
        remove_prerequisite(hass)

    async def do_add_dashboard(call: ServiceCall) -> None:
        state = get_state(hass)
        install_dashboard(hass, bool(state.get(KEY_DASHBOARD_SHOW_IN_SIDEBAR, False)))

    async def do_remove_dashboard(call: ServiceCall) -> None:
        remove_dashboard(hass)

    async def do_add_sidebar(call: ServiceCall) -> None:
        install_dashboard(hass, True)

    async def do_remove_sidebar(call: ServiceCall) -> None:
        install_dashboard(hass, False)

    async def do_rebuild_dashboard(call: ServiceCall) -> None:
        await async_write_dashboard_file(hass)
        persistent_notification.async_create(
            hass,
            "RFLink Raw Tools dashboard rebuilt from the current Home Assistant entity registry. If the dashboard still has missing entities, run reset_ui, restart Core, and delete/re-add the integration once if needed.",
            title="RFLink Raw Tools Dashboard Rebuilt",
            notification_id="rflink_raw_dashboard_rebuilt",
        )

    async def do_reset_ui(call: ServiceCall) -> None:
        removed = await async_reset_ui_registry(hass)
        await async_write_dashboard_file(hass)
        persistent_notification.async_create(
            hass,
            (
                "RFLink Raw Tools UI reset complete. "
                f"Removed {len(removed)} stale entities. "
                "Restart Home Assistant if the device page does not update immediately."
            ),
            title="RFLink Raw Tools UI Reset",
            notification_id="rflink_raw_ui_reset",
        )

    hass.services.async_register(DOMAIN, "send_raw", send_raw, schema=SEND_RAW_SCHEMA)
    hass.services.async_register(DOMAIN, "send_protocol", send_protocol, schema=SEND_PROTOCOL_SCHEMA)
    hass.services.async_register(DOMAIN, "send_stored_raw", send_stored_raw)
    hass.services.async_register(DOMAIN, "send_stored_protocol", send_stored_protocol)
    hass.services.async_register(DOMAIN, "ping_gateway", do_ping_gateway)
    hass.services.async_register(DOMAIN, "version_gateway", do_version_gateway)
    hass.services.async_register(DOMAIN, "ping", do_ping_gateway)
    hass.services.async_register(DOMAIN, "version", do_version_gateway)
    hass.services.async_register(DOMAIN, "update_from_github", do_update)
    hass.services.async_register(DOMAIN, "restore_last_update", do_restore)
    hass.services.async_register(DOMAIN, "install_prerequisite", do_install_prerequisite)
    hass.services.async_register(DOMAIN, "remove_prerequisite", do_remove_prerequisite)
    hass.services.async_register(DOMAIN, "add_dashboard", do_add_dashboard)
    hass.services.async_register(DOMAIN, "remove_dashboard", do_remove_dashboard)
    hass.services.async_register(DOMAIN, "add_sidebar", do_add_sidebar)
    hass.services.async_register(DOMAIN, "remove_sidebar", do_remove_sidebar)
    hass.services.async_register(DOMAIN, "rebuild_dashboard", do_rebuild_dashboard)
    hass.services.async_register(DOMAIN, "reset_ui", do_reset_ui)

    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up RFLink Raw Tools config entry."""
    await async_initialize_store(hass)
    sync_prerequisite_state(hass)
    await async_reset_ui_registry(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_write_dashboard_file(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload RFLink Raw Tools config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
