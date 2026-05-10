# RFLink Raw Tools

<p align="center"><img src="assets/logo.png" alt="RFLink Raw Tools" width="120"></p>

Version: **0.0.1**

## UI/UX reset

This build is a clean app baseline. It stops using the Home Assistant device page, generated Lovelace dashboard, fake action switches, and self-updater as the main experience.

The user experience is now:

```text
Open RFLink Raw Tools from the sidebar.
Type or paste a command.
Click Send.
See success/error.
```

## Design principles

1. **App first** — RFLink Raw Tools is a sidebar app, not a long entity list.
2. **No fake switches** — one-time actions are app buttons and services.
3. **No generated dashboard dependency** — no Lovelace entity drift.
4. **No self-update workflow** — use HACS or the terminal installer.
5. **No configuration.yaml editing** — the user’s existing RFLink setup stays user-managed.
6. **No cache artifacts** — no `__pycache__`, no `.pyc`, no stale `button.py`.

## App pages

```text
Send   - raw command box, repeat, delay, send
Learn  - simple learning workflow for non-coders
Debug  - ping, version, RFDEBUG, QRFDEBUG
Setup  - connection/status and install/update guidance
```

## Install

### HACS custom repository

Add this repository as a custom integration repository in HACS, install it, restart Home Assistant, then add the integration:

```text
Settings -> Devices & services -> Add integration -> RFLink Raw Tools
```

### Manual terminal install

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

Then add the integration if it is not already added:

```text
Settings -> Devices & services -> Add integration -> RFLink Raw Tools
```

## RFLink requirement

The normal Home Assistant RFLink integration must already be configured and connected.

Example:

```yaml
rflink:
  port: /dev/ttyUSB0
  wait_for_ack: false
  reconnect_interval: 10
```

## Notes on raw commands

Home Assistant’s RFLink command bridge expects a device id and command. The app converts full RFLink-style command strings into that format.

Examples:

```text
10;NewKaku;01a2b3;1;ON;
10;rfdebug;on;
10;PING;
10;VERSION;
```

Some RFLink gateway/control commands depend on what Home Assistant’s RFLink bridge supports in your installed HA version.

## Approved artwork

```text
assets/logo.png md5: 16bad0221d68821784cd5d26a33f2d3c
brand/icon.png md5: 07429242aaec19f7a5c2d031535255ff
```

## QA

This package includes `tests/test_static_package.py` and `QA_REPORT.md`.

Run static checks locally:

```bash
python3 -m py_compile custom_components/rflink_raw/*.py
python3 -m pytest tests
```


## HACS install

This repository is HACS-ready. HACS is the intended install/update channel for the app baseline.

To install with HACS:

```text
HACS -> Integrations -> three dots -> Custom repositories
Repository: https://github.com/michaeldn/ha-rflink-raw-tools
Category: Integration
Add
```

Then install **RFLink Raw Tools**, restart Home Assistant, and add the integration:

```text
Settings -> Devices & services -> Add integration -> RFLink Raw Tools
```

The terminal `install.sh` remains as a recovery/manual install path.

## Panel overwrite fix

If setup fails with:

```text
ValueError: Overwriting panel rflink-raw-tools
```

Home Assistant already has the RFLink Raw Tools sidebar panel registered from a prior setup attempt or duplicate entry.

This build makes panel setup idempotent by removing the existing `rflink-raw-tools` panel before registering it again.

Also keep only one integration entry:

```text
Settings -> Devices & services -> RFLink Raw Tools
```


## App logo/static asset fix

The app panel displays the header logo from:

```text
/api/rflink_raw/static/logo.png
```

That path maps to:

```text
custom_components/rflink_raw/www/logo.png
```

This package places the approved logo and icon in both locations:

```text
custom_components/rflink_raw/www/logo.png
custom_components/rflink_raw/www/icon.png
custom_components/rflink_raw/brand/logo.png
custom_components/rflink_raw/brand/icon.png
```

Approved hashes:

```text
logo.png md5: 16bad0221d68821784cd5d26a33f2d3c
icon.png md5: 07429242aaec19f7a5c2d031535255ff
```

If HACS itself shows a blank icon for a custom repository, that can be separate from the Home Assistant integration/app icon. The app header and Home Assistant integration brand files are local assets in this package.
