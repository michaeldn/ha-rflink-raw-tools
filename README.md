# RFLink Raw Tools

RFLink Raw Tools is a Home Assistant custom integration that adds a **Devices & services UI** for RFLink gateway commands.

It also includes a GUI helper to install the normal Home Assistant RFLink prerequisite YAML.

## What this adds

After installation, add it from:

```text
Settings → Devices & services → Add integration → RFLink Raw Tools
```

During setup, the UI can write this prerequisite block into `configuration.yaml` for you:

```yaml
rflink:
  port: /dev/ttyUSB0
  wait_for_ack: false
  reconnect_interval: 10
```

The installer creates a timestamped backup of `configuration.yaml` before writing.

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

## Normal RFLink command UI

The created device includes:

### Text inputs

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

## Easy install from GitHub

In the Home Assistant Terminal, run:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

After Home Assistant restarts:

```text
Settings → Devices & services → Add integration → RFLink Raw Tools
```

## Updating

Run the installer again:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

## Services

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

## Important limitation

This integration sends RFLink gateway text commands.

It does **not** make classic RFLink R48 replay arbitrary `DEBUG;Pulses=...` captures unless the RFLink firmware itself supports a transmit command for that format.
