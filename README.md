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


## HACS/public listing readiness

This repository includes the required HACS metadata and validation workflow files for an integration repository:

```text
hacs.json
.github/workflows/hacs.yml
.github/workflows/hassfest.yml
.github/workflows/static-package.yml
```

For a public HACS default listing, the GitHub repository still needs repository-level metadata that cannot be stored in the code package:

```text
Repository description
Repository topics
GitHub release v0.0.1
Passing HACS validation
Passing Hassfest validation
HACS/default inclusion request
```

See `HACS_PUBLIC_LISTING_CHECKLIST.md`.

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


## RFLink status wording

The app now separates two different checks:

```text
RFLink configured = configuration.yaml has a top-level rflink: block.
RFLink ready      = Home Assistant's RFLink command bridge reports connected.
```

If the first thing you see is:

```text
RFLink configured — test with Ping
```

that is not a setup failure. It means the app found the normal Home Assistant RFLink config and wants you to click **Debug -> Ping gateway** to confirm the live bridge responds.

This replaces the confusing earlier wording:

```text
RFLink not confirmed
```


## Status and Ping behavior

The app no longer keeps showing **Checking RFLink…** if the status call fails. It now shows a clear status/error.

`Debug -> Ping gateway` is now an app-level RFLink status check. It verifies that Home Assistant has loaded the normal RFLink integration without trying to send an invalid gateway-only command through `rflink.send_command`.

Why: Home Assistant's built-in `rflink.send_command` service expects a protocol device id. Calling it as a generic gateway ping can fail with errors like:

```text
'id'
required key not provided @ data['device_id']
```

For real hardware testing, use the **Send** page with a learned RFLink device command.


## Setup return fix

This package fixes:

```text
Integration 'rflink_raw' did not return boolean if setup was successful.
```

Cause: the previous generated `__init__.py` compiled, but `ping_gateway` and `version_gateway` were accidentally dedented to module scope. That ended `async_setup` early, so Home Assistant received `None`.

The fix rewrites `__init__.py` cleanly and adds a static AST test that catches leaked service handlers.


## Websocket/status and debug switch UX fix

This package fixes three app issues:

```text
1. Status unavailable / Unknown command from missing websocket registration.
2. 10;PING; showing Unknown command from the raw Send page.
3. RFDEBUG/QRFDEBUG shown as on/off buttons instead of switches.
```

Backend registration is now idempotent and called from both `async_setup` and `async_setup_entry`.

The Debug page now uses switch-style toggles:

```text
RFDEBUG   on/off switch
QRFDEBUG  on/off switch
```

The Send page no longer defaults to `10;PING;`. Ping and Version live on the Debug page as app status checks.


## Send tab guard for Ping/Version and stale saved values

The Send tab now guards against the confusing `Unknown command` loop:

```text
10;PING;
10;VERSION;
PING
VERSION
```

Those are handled as app-level Debug/status actions instead of being sent to Home Assistant's `rflink.send_command` service as device commands.

The app also clears old saved `10;PING;` or `10;VERSION;` values from browser localStorage on load.

Use the Send tab only for learned RFLink device commands, for example:

```text
10;NewKaku;01a2b3;1;ON;
10;NewKaku;01a2b3;1;OFF;
```


## Frontend cache-bust and Send guard verification

This package changes the panel module URL to include a build query string:

```text
rflink-raw-tools-panel.js?v=app-cachebust-send-fix-20260510
```

Visual checks after install:

```text
Send tab has a Clear command button.
Setup tab shows App build: app-cachebust-send-fix-20260510.
```

If those are not visible, the browser is still showing old JavaScript. Use Chrome hard refresh on Mac:

```text
Command + Shift + R
```

Terminal verification:

```bash
sh /config/check-rflink-app-build.sh
```


## Ping button and cache cleanup

The Debug -> Ping gateway button is now a non-throwing app-level status check.

It does not call Home Assistant's `rflink.send_command` with a missing or fake device id, so it should not throw red UI errors. It records one of these messages:

```text
RFLink integration is loaded. Use a learned device command for hardware send testing.
RFLink integration is not loaded yet. Check configuration.yaml and restart Home Assistant.
```

This package also removes Python cache artifacts from the repository and installer output:

```text
__pycache__/
*.pyc
```

Verify on Home Assistant:

```bash
sh /config/check-rflink-app-build.sh
```

Nothing should print under **Cache artifacts check**.



## Debug switch/status UX fix

RFDEBUG/QRFDEBUG switches now update visually immediately, and the labels show Enabled/Disabled.

If RFLink rejects a debug command, the app keeps the local switch state and shows an informational result instead of leaving a persistent red error. Ping/Version also overwrite stale "Unknown command" messages with clean status results.

The Setup page now says **RFLink configuration scan** because it is only a text scan of configuration.yaml, not proof that the app is broken.



## Runtime Python cache check fix

The previous check script said nothing should print under cache artifacts. That was wrong after a Home Assistant restart.

Home Assistant/Python may create runtime bytecode files here:

```text
/config/custom_components/rflink_raw/__pycache__/*.pyc
```

That is normal after Core imports the integration. The real packaging rule is:

```text
The repo/zip should not ship __pycache__ or *.pyc.
The installer should remove any shipped/stale cache files before install.
Runtime cache may appear again after restart.
```

Use:

```bash
sh /config/check-rflink-app-build.sh
```

To remove runtime cache manually:

```bash
sh /config/clean-rflink-runtime-cache.sh
```

It may return after another restart, which is expected.



## Pre-restart install cleanliness check

The installer now checks cache artifacts before Home Assistant restarts.

During install it prints:

```text
Package cache check before cleanup
Package cache check after cleanup
Installed target pre-restart check
```

You can also run this immediately after install and **before** `ha core restart`:

```bash
sh /config/check-rflink-before-restart.sh
```

Expected before restart:

```text
PASS: no __pycache__ or *.pyc in installed target before restart.
```

After restart, Home Assistant/Python may recreate `__pycache__/*.pyc`. That is normal runtime bytecode.



## Installer gated restart

The installer now uses explicit shell checks before restarting Home Assistant Core.

It checks with `find ... | grep -q .` logic:

```text
1. Check downloaded package before cleanup.
2. Remove __pycache__ and *.pyc.
3. Check downloaded package after cleanup.
4. Copy integration into /config/custom_components/rflink_raw.
5. Remove cache artifacts from installed target.
6. Run /config/check-rflink-before-restart.sh.
7. Restart Core only if all checks pass.
```

If a check fails, the installer exits with an error and does **not** run:

```bash
ha core restart
```



## Error-state UX fix

A hard browser refresh reloads JavaScript, but it does not necessarily clear backend app state stored in Home Assistant memory.

The UI now separates:

```text
Active error = only the action the user just clicked.
Backend history = last result/error shown on Setup.
```

The Send tab no longer replays an old backend `Unknown command` as a red banner on page load or refresh.

The Setup page now has:

```text
Clear status
```

which calls:

```text
rflink_raw.clear_status
```

and clears the app's last result, last error, last command, and active UI banner.



## UX state cleanup

This package fixes three user-facing problems:

```text
1. Old "Unknown command" messages no longer reappear as red banners after refresh.
2. RFDEBUG/QRFDEBUG are relabeled as human-readable logging switches.
3. The confusing Learn page is renamed Capture and explains its purpose.
```

Debug labels are now:

```text
Decoded RFLink logging
Raw RF capture logging
```

The switches update immediately and also persist locally in the browser so they do not visually flip off when you change tabs.


## Status API fix

The red persistent `Unknown command` was coming from the frontend status check path, not necessarily from the Send action.

The app no longer depends on the websocket command for status. It now registers:

```text
GET /api/rflink_raw/status
```

The frontend calls that endpoint with Home Assistant's `callApi`, sanitizes old generic RFLink command errors, and never displays backend history as an active red banner on refresh.

If the status API is unavailable, the app shows a non-red status fallback instead of `Unknown command`.



## Software cleanup final

This package separates the app from the old Lovelace dashboard cleanup and fixes the remaining app UX issues:

```text
Send    = real learned device commands only.
Capture = explains how to learn/capture commands from a physical remote.
Debug   = human-readable logging switches with persistent visual state.
Setup   = build/status/history without replaying stale errors as red banners.
```

The app now uses:

```text
GET /api/rflink_raw/status
```

for status instead of the older websocket status path. Generic stale `Unknown command` history is sanitized in both backend and frontend status.

## Helpful tool rebuild

Pages: Send, Captured, Debug, Setup. Captured shows RFLink entity registry entries and recent RFLink log lines. Setup can add a conservative top-level `rflink:` YAML block if missing. Version remains 0.0.1.


## Menu color fix

The Send / Captured / Debug / Setup navigation now uses a Home Assistant-style segmented control. Inactive tabs use the same card/background palette as the page, while the active tab uses the Home Assistant primary color.
