"""Constants for RFLink Raw Tools."""

DOMAIN = "rflink_raw"
NAME = "RFLink Raw Tools"
VERSION = "0.0.1"

PLATFORMS = ["switch", "text", "number"]

STORAGE_VERSION = 1
STORAGE_KEY = "rflink_raw_tools_state"

DATA_STATE = "state"
DATA_STORE = "store"
SIGNAL_STATE_UPDATED = f"{DOMAIN}_state_updated"

ADMIN_DEVICE_IDENTIFIER = "rflink_raw_tools_admin"
ADMIN_DEVICE_NAME = "RFLink Raw Tools"

COMMAND_DEVICE_IDENTIFIER = "rflink_raw_tools_command_center"
COMMAND_DEVICE_NAME = "RFLink Raw Tools Command Center"

MANUFACTURER = "Custom Home Assistant"
MODEL = "RFLink Raw Tools"

KEY_RAW_COMMAND = "raw_command"
KEY_PROTOCOL_DEVICE_ID = "protocol_device_id"
KEY_PROTOCOL_COMMAND = "protocol_command"
KEY_REPEAT = "repeat"
KEY_DELAY_MS = "delay_ms"

KEY_PREREQ_PORT = "prereq_port"
KEY_PREREQ_WAIT_FOR_ACK = "prereq_wait_for_ack"
KEY_PREREQ_RECONNECT_INTERVAL = "prereq_reconnect_interval"
KEY_PREREQ_INSTALLED = "prereq_installed"

KEY_DASHBOARD_ENABLED = "dashboard_enabled"
KEY_DASHBOARD_SHOW_IN_SIDEBAR = "dashboard_show_in_sidebar"

KEY_LAST_UPDATE_BACKUP = "last_update_backup"

MANAGED_BLOCK_START = "# BEGIN RFLink Raw Tools managed RFLink prerequisite"
MANAGED_BLOCK_END = "# END RFLink Raw Tools managed RFLink prerequisite"

MANAGED_DASHBOARD_BLOCK_START = "# BEGIN RFLink Raw Tools managed dashboard"
MANAGED_DASHBOARD_BLOCK_END = "# END RFLink Raw Tools managed dashboard"

DASHBOARD_KEY = "rflink-raw-tools"
DASHBOARD_FILENAME = "rflink_raw_dashboard.yaml"
DASHBOARD_TITLE = "RFLink Raw Tools"
DASHBOARD_ICON = "mdi:radio-tower"
