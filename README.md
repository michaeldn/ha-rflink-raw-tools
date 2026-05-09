# RFLink Raw Tools

<p align="center"><img src="assets/logo.png" alt="RFLink Raw Tools" width="220"></p>

RFLink Raw Tools is a Home Assistant custom integration for RFLink command sending, RFDEBUG/QRFDEBUG, dashboard/sidebar setup, and UI-based updates.

## v0.1.2 Safe Undo Build

This build is designed so every managed change has a matching undo path.

### UI undo switches

| Thing it does | On | Off / undo |
|---|---|---|
| Install RFLink prerequisite | Writes a marked RFLink block to `configuration.yaml` | Removes only that marked block |
| Add dashboard | Writes the marked Lovelace dashboard block and dashboard files | Removes the marked block, dashboard YAML, and logo folder |
| Add to sidebar | Updates the marked dashboard block with `show_in_sidebar: true` | Updates the marked dashboard block with `show_in_sidebar: false` |
| Require admin | Updates the marked dashboard block with `require_admin: true` | Updates it back to `false` |
| GitHub update | Backs up the current integration/dashboard/logo files first | `Undo Last GitHub Update` restores that backup |

### Full undo script

This package includes:

```text
undo-rflink-raw-tools.sh
```

It disables the custom integration folder, removes RFLink Raw Tools managed YAML blocks, removes dashboard/logo files, removes RFLink Raw Tools storage dashboard entries, and backs everything up first.

## First install

Open the Home Assistant Terminal add-on and run:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

Then add the integration:

```text
Settings → Devices & services → Add integration → RFLink Raw Tools
```

Safe defaults now do **not** write the prerequisite or dashboard automatically. Use the switches after the integration loads:

```text
Install RFLink Prerequisite
Add Dashboard
Add To Sidebar
```

## Local development apply

The included `apply-local.sh` expects the local repo here:

```text
/Users/michaeldumas/Projects/ha-rflink-raw-tools
```

## Important limitation

This integration sends RFLink gateway text commands. It does not make classic RFLink R48 replay arbitrary `DEBUG;Pulses=...` captures unless the RFLink firmware itself supports a transmit command for that format.
