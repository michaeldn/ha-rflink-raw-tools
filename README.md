# RFLink Raw Tools

RFLink Raw Tools is a Home Assistant custom integration that adds a **Devices & services UI** for RFLink gateway commands.

It also includes a GUI helper to install the normal Home Assistant RFLink prerequisite YAML.

## Linux / Home Assistant OS install

These are the primary install instructions.

Open the Home Assistant Terminal and run:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

After Home Assistant restarts, add the integration from the UI:

```text
Settings → Devices & services → Add integration → RFLink Raw Tools
```

During setup, leave **Install prerequisite** enabled unless you already have a working `rflink:` block in `configuration.yaml`.

Use these values for a typical HAOS RFLink USB/IP setup:

```text
RFLink Prerequisite Port: /dev/ttyUSB0
RFLink Prerequisite Wait For ACK: off
RFLink Prerequisite Reconnect Interval: 10
```

Then check and restart Home Assistant Core:

```bash
ha core check
ha core restart
```

## How to Run

After installation, open the created device:

```text
Settings → Devices & services → Devices → RFLink Raw Tools
```

The device contains controls for installing the RFLink prerequisite, sending RFLink commands, and capturing RF debug output.

### Run a basic RFLink test

Press:

```text
RFLink Ping
```

Then check logs:

```bash
ha core logs | grep -i -E "rflink|rflink_raw|PING|PONG|Connected to Rflink"
```

### Send a direct RFLink command

Set:

```text
RFLink Raw Command = 10;QRFDEBUG=ON;
RFLink Repeat Count = 1
RFLink Repeat Delay = 250
```

Then press:

```text
Send RFLink Raw Command
```

To stop QRFDEBUG, set:

```text
RFLink Raw Command = 10;QRFDEBUG=OFF;
```

Then press:

```text
Send RFLink Raw Command
```

### Send a normal RFLink protocol command

Set:

```text
RFLink Protocol Device ID = newkaku_0cac142_3
RFLink Protocol Command = on
RFLink Repeat Count = 3
RFLink Repeat Delay = 250
```

Then press:

```text
Send RFLink Protocol Command
```

### Capture RFLink debug data

Use one of the built-in buttons or switches:

```text
Start RFDEBUG Capture
Stop RFDEBUG Capture
Start QRFDEBUG Capture
Stop QRFDEBUG Capture
RFLink RFDEBUG
RFLink QRFDEBUG
```

Then watch the logs:

```bash
ha core logs --follow | grep -i -E "rflink|debug|pulses|raw|decoded packet|got packet"
```

## Prerequisite

The normal Home Assistant RFLink integration must already be working before RFLink Raw Tools can send RFLink commands.

Example `configuration.yaml`:

```yaml
rflink:
  port: /dev/ttyUSB0
  wait_for_ack: false
  reconnect_interval: 10
```

You should see this in the Home Assistant logs:

```text
Connected to Rflink
```

## GUI prerequisite installer

RFLink Raw Tools can install/update the prerequisite block for you.

In the RFLink Raw Tools setup UI, keep **Install prerequisite** enabled and set:

```text
RFLink Prerequisite Port = /dev/ttyUSB0
RFLink Prerequisite Wait For ACK = off
RFLink Prerequisite Reconnect Interval = 10
```

Then complete setup.

The installer writes this block to `/config/configuration.yaml` and creates a timestamped backup first:

```yaml
rflink:
  port: /dev/ttyUSB0
  wait_for_ack: false
  reconnect_interval: 10
```

You can also install/update it later from the created device:

```text
Settings → Devices & services → Devices → RFLink Raw Tools
```

Set the prerequisite entities:

```text
RFLink Prerequisite Port
RFLink Prerequisite Wait For ACK
RFLink Prerequisite Reconnect Interval
```

Then press:

```text
Install RFLink Prerequisite YAML
```

After installing the prerequisite YAML, run:

```bash
ha core check
ha core restart
```

## What this adds

The created device includes:

### Text inputs

- **RFLink Prerequisite Port** — example: `/dev/ttyUSB0`
- **RFLink Raw Command** — default: `10;PING;`
- **RFLink Protocol Device ID** — example: `newkaku_0cac142_3`
- **RFLink Protocol Command** — example: `on`, `off`, `UP`, `DOWN`, `STOP`, `PAIR`

### Repeat controls

- **RFLink Repeat Count** — number of times to send the command
- **RFLink Repeat Delay** — delay between repeated sends, in milliseconds

### Buttons

- **Install RFLink Prerequisite YAML**
- **Send RFLink Raw Command**
- **Send RFLink Protocol Command**
- **RFLink Ping**
- **RFLink Version**
- **RFLink Status**
- **Start RFDEBUG Capture**
- **Stop RFDEBUG Capture**
- **Start QRFDEBUG Capture**
- **Stop QRFDEBUG Capture**

### Switches

- **RFLink Prerequisite Wait For ACK**
- **RFLink RFDEBUG**
- **RFLink QRFDEBUG**

### Sensors

- **RFLink Prerequisite Status**
- **RFLink Last Command**
- **RFLink Last Response**
- **RFLink Last Error**

## Updating from Linux / Home Assistant OS

Run the installer again:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

## Manual install

Manual install is only needed if the installer command is not available.

Copy this folder from the repository:

```text
custom_components/rflink_raw
```

to Home Assistant:

```text
/config/custom_components/rflink_raw
```

Restart Home Assistant:

```bash
ha core restart
```

Then add it from:

```text
Settings → Devices & services → Add integration → RFLink Raw Tools
```

## Developer install from macOS, Windows, or Linux

This is only for developing or editing the integration before pushing to GitHub.

Clone the repo:

```bash
git clone https://github.com/michaeldn/ha-rflink-raw-tools.git
cd ha-rflink-raw-tools
```

After editing, push to GitHub:

```bash
git add .
git commit -m "Update RFLink Raw Tools"
git push
```

Then update Home Assistant OS using the Linux install command:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

## Services

### Send raw command once

```yaml
action: rflink_raw.send_raw
data:
  raw_command: "10;QRFDEBUG=ON;"
```

### Send raw command with repeat

```yaml
action: rflink_raw.send_raw
data:
  raw_command: "10;NewKaku;0cac142;3;ON;"
  repeat: 3
  delay_ms: 250
```

### Send RFLink protocol command with repeat

```yaml
action: rflink_raw.send_protocol
data:
  device_id: "newkaku_0cac142_3"
  command: "on"
  repeat: 3
  delay_ms: 250
```

### Turn RFDEBUG on/off

```yaml
action: rflink_raw.rfdebug
data:
  mode: "on"
```

```yaml
action: rflink_raw.rfdebug
data:
  mode: "off"
```

### Turn QRFDEBUG on/off

```yaml
action: rflink_raw.qrfdebug
data:
  mode: "on"
```

```yaml
action: rflink_raw.qrfdebug
data:
  mode: "off"
```

## Important limitation

This integration sends RFLink gateway text commands.

It does **not** make classic RFLink R48 replay arbitrary `DEBUG;Pulses=...` captures unless the RFLink firmware itself supports a transmit command for that format.

For classic RFLink Gateway firmware, normal transmit commands require a supported RFLink protocol, such as:

```text
10;NewKaku;0cac142;3;ON;
10;EV1527;000080;0;ON;
10;RTS;1a602a;0;ON;
```

## Troubleshooting

Check the logs:

```bash
ha core logs | grep -i -E "rflink|rflink_raw|Connected to Rflink|error"
```

If the RFLink Raw Tools integration is loaded, you should see:

```text
RFLink Raw Tools services registered
```

If commands fail, confirm the normal RFLink integration is connected first.
