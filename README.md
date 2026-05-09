# RFLink Raw Tools

RFLink Raw Tools is a Home Assistant custom integration that adds a **Devices & services UI** for RFLink gateway commands.

It is meant to make RFLink easier to use from Home Assistant without opening the Windows RFLink Loader or manually writing to `/dev/ttyUSB0`.

## What this adds

After installation, add it from:

```text
Settings → Devices & services → Add integration → RFLink Raw Tools
```

It creates one Home Assistant device named:

```text
RFLink Raw Tools
```

The device includes:

### Text inputs

- **RFLink Raw Command** — default: `10;PING;`
- **RFLink Protocol Device ID** — example: `newkaku_0cac142_3`
- **RFLink Protocol Command** — example: `on`, `off`, `UP`, `DOWN`, `STOP`, `PAIR`

### Repeat controls

- **RFLink Repeat Count** — number of times to send the command
- **RFLink Repeat Delay** — delay between repeated sends, in milliseconds

### Buttons

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

- **RFLink RFDEBUG**
- **RFLink QRFDEBUG**

### Sensors

- **RFLink Last Command**
- **RFLink Last Response**
- **RFLink Last Error**

## Prerequisite

The normal Home Assistant RFLink integration must already be working.

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

## Manual install

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

## Updating

Run the installer again:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

## Using the UI

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

This will send the RFLink command three times with a 250 ms delay between transmissions.

## Services

The integration also exposes Home Assistant actions.

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
