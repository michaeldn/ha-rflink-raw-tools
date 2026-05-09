"""Button platform for RFLink Raw Tools."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components import persistent_notification
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import (
    DEVICE_IDENTIFIER,
    DEVICE_NAME,
    DOMAIN,
    KEY_DELAY_MS,
    KEY_PREREQ_PORT,
    KEY_PREREQ_RECONNECT_INTERVAL,
    KEY_PREREQ_WAIT_FOR_ACK,
    KEY_PROTOCOL_COMMAND,
    KEY_PROTOCOL_DEVICE_ID,
    KEY_RAW_COMMAND,
    KEY_REPEAT,
    MANUFACTURER,
    MODEL,
    VERSION,
)
from .helpers import async_send_direct_command, async_send_protocol_command
from .prereq import install_rflink_prerequisite
from .store import get_state, update_state


@dataclass(frozen=True, kw_only=True)
class RFLinkRawButtonDescription(EntityDescription):
    """Description for an RFLink raw tools button."""

    command: str | None = None
    action_type: str = "direct"


BUTTONS: tuple[RFLinkRawButtonDescription, ...] = (
    RFLinkRawButtonDescription(
        key="setup_load_default_prerequisite_values",
        name="Setup Load Default Prerequisite Values",
        icon="mdi:tune-variant",
        action_type="load_default_prereq",
    ),
    RFLinkRawButtonDescription(
        key="setup_install_prerequisite",
        name="Setup Install RFLink Prerequisite YAML",
        icon="mdi:file-cog-outline",
        action_type="install_prerequisite",
    ),
    RFLinkRawButtonDescription(
        key="control_send_raw_text",
        name="Control Send RFLink Raw Command",
        icon="mdi:send",
        action_type="send_raw_text",
    ),
    RFLinkRawButtonDescription(
        key="control_send_protocol_text",
        name="Control Send RFLink Protocol Command",
        icon="mdi:remote",
        action_type="send_protocol_text",
    ),
    RFLinkRawButtonDescription(
        key="help_load_example_raw",
        name="Help Load Example Raw Command",
        icon="mdi:code-tags",
        action_type="load_example_raw",
    ),
    RFLinkRawButtonDescription(
        key="help_load_example_protocol",
        name="Help Load Example Protocol Command",
        icon="mdi:gesture-tap-button",
        action_type="load_example_protocol",
    ),
    RFLinkRawButtonDescription(
        key="help_show_logs",
        name="Help Show Log Commands",
        icon="mdi:text-box-search-outline",
        action_type="show_logs_help",
    ),
    RFLinkRawButtonDescription(
        key="help_show_find_device",
        name="Help Show Find Device Steps",
        icon="mdi:radar",
        action_type="show_find_device_help",
    ),
    RFLinkRawButtonDescription(
        key="help_show_dashboard_setup",
        name="Help Show Dashboard Setup",
        icon="mdi:view-dashboard-edit-outline",
        action_type="show_dashboard_help",
    ),
    RFLinkRawButtonDescription(key="debug_ping", name="Debug RFLink Ping", icon="mdi:access-point-check", command="10;PING;"),
    RFLinkRawButtonDescription(key="debug_version", name="Debug RFLink Version", icon="mdi:information-outline", command="10;VERSION;"),
    RFLinkRawButtonDescription(key="debug_status", name="Debug RFLink Status", icon="mdi:list-status", command="10;STATUS;"),
    RFLinkRawButtonDescription(key="debug_rfdebug_on", name="Debug Start RFDEBUG Capture", icon="mdi:radio-tower", command="10;RFDEBUG=ON;"),
    RFLinkRawButtonDescription(key="debug_rfdebug_off", name="Debug Stop RFDEBUG Capture", icon="mdi:radio-tower-off", command="10;RFDEBUG=OFF;"),
    RFLinkRawButtonDescription(key="debug_qrfdebug_on", name="Debug Start QRFDEBUG Capture", icon="mdi:signal", command="10;QRFDEBUG=ON;"),
    RFLinkRawButtonDescription(key="debug_qrfdebug_off", name="Debug Stop QRFDEBUG Capture", icon="mdi:signal-off", command="10;QRFDEBUG=OFF;"),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up RFLink Raw Tools buttons."""
    async_add_entities(RFLinkRawButton(hass, entry.entry_id, description) for description in BUTTONS)


class RFLinkRawButton(ButtonEntity):
    """RFLink command button."""

    _attr_has_entity_name = False

    def __init__(self, hass, entry_id: str, description: RFLinkRawButtonDescription) -> None:
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
        state = get_state(self.hass)

        if self.entity_description.action_type == "load_default_prereq":
            update_state(
                self.hass,
                **{
                    KEY_PREREQ_PORT: "/dev/ttyUSB0",
                    KEY_PREREQ_WAIT_FOR_ACK: False,
                    KEY_PREREQ_RECONNECT_INTERVAL: 10,
                },
            )
            persistent_notification.async_create(
                self.hass,
                """Default RFLink prerequisite values loaded:
- Port: /dev/ttyUSB0
- Wait For ACK: off
- Reconnect Interval: 10

Next press **Setup Install RFLink Prerequisite YAML**.""",
                title="RFLink Raw Tools • Defaults Loaded",
                notification_id="rflink_raw_defaults",
            )
            return

        if self.entity_description.action_type == "install_prerequisite":
            install_rflink_prerequisite(
                self.hass,
                state[KEY_PREREQ_PORT],
                bool(state[KEY_PREREQ_WAIT_FOR_ACK]),
                int(state[KEY_PREREQ_RECONNECT_INTERVAL]),
            )
            persistent_notification.async_create(
                self.hass,
                """RFLink prerequisite YAML was written to configuration.yaml.

Next steps:
1. Go to **Settings → System → Logs** if you want to review messages.
2. Run `ha core check`.
3. Restart Home Assistant Core.
4. Open the RFLink Raw Tools dashboard/device page.""",
                title="RFLink Raw Tools • Prerequisite Installed",
                notification_id="rflink_raw_prereq_done",
            )
            return

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

        if self.entity_description.action_type == "load_example_raw":
            update_state(
                self.hass,
                **{
                    KEY_RAW_COMMAND: "10;NewKaku;0cac142;3;ON;",
                    KEY_REPEAT: 3,
                    KEY_DELAY_MS: 250,
                },
            )
            persistent_notification.async_create(
                self.hass,
                """Loaded an example raw RFLink command into the control fields:

10;NewKaku;0cac142;3;ON;

You can copy/edit it from the **Control RFLink Raw Command** text field, then press **Control Send RFLink Raw Command**.""",
                title="RFLink Raw Tools • Example Raw Command Loaded",
                notification_id="rflink_raw_example_raw",
            )
            return

        if self.entity_description.action_type == "load_example_protocol":
            update_state(
                self.hass,
                **{
                    KEY_PROTOCOL_DEVICE_ID: "newkaku_0cac142_3",
                    KEY_PROTOCOL_COMMAND: "on",
                    KEY_REPEAT: 3,
                    KEY_DELAY_MS: 250,
                },
            )
            persistent_notification.async_create(
                self.hass,
                """Loaded an example RFLink protocol command into the control fields:

Device ID: newkaku_0cac142_3
Command: on
Repeat: 3
Delay: 250 ms

Next press **Control Send RFLink Protocol Command**.""",
                title="RFLink Raw Tools • Example Protocol Command Loaded",
                notification_id="rflink_raw_example_protocol",
            )
            return

        if self.entity_description.action_type == "show_logs_help":
            persistent_notification.async_create(
                self.hass,
                """**Where to see logs**

- UI: **Settings → System → Logs**
- Terminal command: `ha core logs | grep -i -E "rflink|rflink_raw|debug|pulses|raw"`
- Follow live logs: `ha core logs --follow | grep -i -E "rflink|debug|pulses|raw"`

Use the **Debug** buttons/switches first, then look here for packets and responses.""",
                title="RFLink Raw Tools • Log Commands",
                notification_id="rflink_raw_log_help",
            )
            return

        if self.entity_description.action_type == "show_find_device_help":
            persistent_notification.async_create(
                self.hass,
                """**How to find a device / packet**

1. Press **Debug Start QRFDEBUG Capture**.
2. Press the remote button or trigger the RF device.
3. Open logs from **Settings → System → Logs** or run the live log command.
4. Look for supported decoded packets such as `RTS`, `NewKaku`, `EV1527`, etc.
5. If Home Assistant sees a supported packet, it can auto-create a device/entity.
6. If you only see raw/debug pulses, RFLink may not support auto-adding that device type.

When finished, press **Debug Stop QRFDEBUG Capture**.""",
                title="RFLink Raw Tools • Find Device Steps",
                notification_id="rflink_raw_find_device_help",
            )
            return

        if self.entity_description.action_type == "show_dashboard_help":
            persistent_notification.async_create(
                self.hass,
                """**Cleaner second page / dashboard**

This package installs a dashboard file at `/config/rflink_raw_dashboard.yaml` and a logo at `/config/www/rflink_raw/logo.png`.

To use it in Home Assistant:
1. Go to **Settings → Dashboards**.
2. Add a new dashboard.
3. Choose YAML mode or import the file contents from `/config/rflink_raw_dashboard.yaml`.
4. Save it as your dedicated RFLink Raw Tools page.

This gives you a cleaner second page than the default device screen.""",
                title="RFLink Raw Tools • Dashboard Setup",
                notification_id="rflink_raw_dashboard_help",
            )
            return

        await async_send_direct_command(self.hass, self.entity_description.command, 1, 250)
