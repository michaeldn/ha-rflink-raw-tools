"""Constants for RFLink Raw Tools."""

DOMAIN = "rflink_raw"
NAME = "RFLink Raw Tools"

PLATFORMS = ["button", "switch", "text", "number", "sensor"]

DATA_STATE = "state"

DEVICE_IDENTIFIER = "rflink_raw_tools_controller"
DEVICE_NAME = "RFLink Raw Tools"
MANUFACTURER = "Custom Home Assistant"
MODEL = "RFLink Command UI"
VERSION = "0.8.0"

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
KEY_UPDATE_STATUS = "update_status"

KEY_LAST_COMMAND = "last_command"
KEY_LAST_RESPONSE = "last_response"
KEY_LAST_ERROR = "last_error"

MANAGED_BLOCK_START = "# BEGIN RFLink Raw Tools managed RFLink prerequisite"
MANAGED_BLOCK_END = "# END RFLink Raw Tools managed RFLink prerequisite"
