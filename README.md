# RFLink Raw Tools

Home Assistant custom integration that adds a UI layer for RFLink gateway commands.

## What this adds

Install it from **Settings → Devices & services → Add integration → RFLink Raw Tools**.

It creates one Home Assistant device named **RFLink Raw Tools** with:

### Text inputs

- **RFLink Raw Command** — default `10;PING;`
- **RFLink Protocol Device ID** — example `newkaku_0cac142_3`
- **RFLink Protocol Command** — example `on`, `off`, `UP`, `DOWN`, `STOP`, `PAIR`

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

## Normal RFLink integration required

Keep your normal Home Assistant RFLink integration configured:

```yaml
rflink:
  port: /dev/ttyUSB0
  wait_for_ack: false
  reconnect_interval: 10
```

You do **not** need `rflink_raw:` in YAML when installing through the UI.

## Install manually

Copy:

```text
custom_components/rflink_raw
```

to:

```text
/config/custom_components/rflink_raw
```

Restart Home Assistant.

Then add it through:

```text
Settings → Devices & services → Add integration → RFLink Raw Tools
```

## Services also included

```yaml
action: rflink_raw.send_raw
data:
  raw_command: "10;QRFDEBUG=ON;"
```

```yaml
action: rflink_raw.send_protocol
data:
  device_id: "newkaku_0cac142_3"
  command: "on"
```

## Limitation

This sends RFLink gateway text commands. It does not make classic RFLink R48 replay arbitrary `DEBUG;Pulses=...` captures unless the firmware itself supports a transmit command for that format.
