"""Constants for RFLink Raw Tools."""

DOMAIN = "rflink_raw"
NAME = "RFLink Raw Tools"

PLATFORMS = ["button", "switch", "text", "number", "sensor"]

STORAGE_VERSION = 1
STORAGE_KEY = "rflink_raw_tools_state"

DATA_STATE = "state"
DATA_STORE = "store"

DEVICE_IDENTIFIER = "rflink_raw_tools_admin"
DEVICE_NAME = "RFLink Raw Tools"
COMMAND_DEVICE_IDENTIFIER = "rflink_raw_tools_command_center"
COMMAND_DEVICE_NAME = "RFLink Raw Tools Command Center"
MANUFACTURER = "Custom Home Assistant"
MODEL = "RFLink Command UI"
VERSION = "0.1.3"

ATTR_RAW_COMMAND = "raw_command"
ATTR_MODE = "mode"
ATTR_REPEAT = "repeat"
ATTR_DELAY_MS = "delay_ms"

KEY_RAW_COMMAND = "raw_command"
KEY_PROTOCOL_DEVICE_ID = "protocol_device_id"
KEY_PROTOCOL_COMMAND = "protocol_command"
KEY_REPEAT = "repeat"
KEY_DELAY_MS = "delay_ms"

KEY_PREREQ_PORT = "prereq_port"
KEY_PREREQ_WAIT_FOR_ACK = "prereq_wait_for_ack"
KEY_PREREQ_RECONNECT_INTERVAL = "prereq_reconnect_interval"
KEY_PREREQ_STATUS = "prereq_status"
KEY_PREREQ_INSTALLED = "prereq_installed"

KEY_DASHBOARD_ENABLED = "dashboard_enabled"
KEY_DASHBOARD_SHOW_IN_SIDEBAR = "dashboard_show_in_sidebar"
KEY_DASHBOARD_REQUIRE_ADMIN = "dashboard_require_admin"
KEY_DASHBOARD_STATUS = "dashboard_status"

KEY_UPDATE_STATUS = "update_status"
KEY_UPDATE_BACKUP_PATH = "update_backup_path"

KEY_LAST_COMMAND = "last_command"
KEY_LAST_RESPONSE = "last_response"
KEY_LAST_ERROR = "last_error"

MANAGED_BLOCK_START = "# BEGIN RFLink Raw Tools managed RFLink prerequisite"
MANAGED_BLOCK_END = "# END RFLink Raw Tools managed RFLink prerequisite"

MANAGED_DASHBOARD_BLOCK_START = "# BEGIN RFLink Raw Tools managed dashboard"
MANAGED_DASHBOARD_BLOCK_END = "# END RFLink Raw Tools managed dashboard"
DASHBOARD_KEY = "rflink-raw-tools"
DASHBOARD_FILENAME = "rflink_raw_dashboard.yaml"
DASHBOARD_TITLE = "RFLink Raw Tools"
DASHBOARD_ICON = "mdi:radio-tower"
DASHBOARD_URL = "/rflink-raw-tools/rflink-start"
