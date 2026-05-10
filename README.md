# RFLink Raw Tools

<p align="center"><img src="assets/logo.png" alt="RFLink Raw Tools" width="120"></p>

Version: **0.0.1**

## Start here / index

1. [What this integration does](#what-this-integration-does)
2. [Prerequisite](#prerequisite)
3. [Install](#install)
4. [Expected clean Home Assistant state](#expected-clean-home-assistant-state)
5. [Reset UI after updates](#reset-ui-after-updates)
6. [Sidebar/dashboard behavior](#sidebardashboard-behavior)
7. [No-Press UI rule](#no-press-ui-rule)
8. [Emergency undo](#emergency-undo)
9. [Troubleshooting](#troubleshooting)

## What this integration does

RFLink Raw Tools adds a Home Assistant UI and services for working with RFLink commands.

It provides:

- RFLink prerequisite setup helper
- RFLink dashboard/sidebar helper
- raw RFLink command sending
- protocol command sending
- RFDEBUG / QRFDEBUG controls
- GitHub update helper
- UI reset helper for stale Home Assistant entities

## Prerequisite

The normal Home Assistant RFLink integration must already be working.

Example `configuration.yaml`:

```yaml
rflink:
  port: /dev/ttyUSB0
  wait_for_ack: false
  reconnect_interval: 10
```

Example RFLink platforms:

```yaml
light:
  - platform: rflink
    automatic_add: true

sensor:
  - platform: rflink
    automatic_add: true
```

RFLink Raw Tools does not replace the normal Home Assistant RFLink integration. It sits beside it.

## Install

Run from the Home Assistant Terminal add-on:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

Then add the integration:

```text
Settings -> Devices & services -> Add integration -> RFLink Raw Tools
```

Do not click **Add entry** again after it is installed. That creates a duplicate integration entry.

## Expected clean Home Assistant state

A clean install should show:

```text
Integration entries:
RFLink Raw Tools                         one entry only

Devices:
RFLink Raw Tools                         setup/admin device
RFLink Raw Tools Command Center          command/debug device
```

Two devices are expected. Two integration entries are not.

Expected entity count may change slightly as the integration evolves, but stale old entities should not remain after a reset.

## Reset UI after updates

Home Assistant keeps entity registry entries from older builds. If the integration UI changes, old controls can remain until the UI registry is reset.

Use this after updates when controls look wrong, duplicated, grayed out, or stale.

### Preferred reset method

Use Home Assistant's built-in action/service:

```text
Developer Tools -> Actions
```

Select:

```text
RFLink Raw Tools: Reset RFLink Raw Tools UI
```

or service name:

```text
rflink_raw.reset_ui
```

Then restart Home Assistant Core:

```bash
ha core restart
```

### Terminal script reset method

The installer also copies this script to `/config`:

```bash
sh /config/reset-rflink-raw-ui.sh
ha core restart
```

Important: some Home Assistant Terminal add-on containers do not include `python3`. If the script says Python is unavailable, use the preferred reset method above:

```text
Developer Tools -> Actions -> rflink_raw.reset_ui
```

### What reset removes

The reset removes stale RFLink Raw Tools registry entities from old builds, especially:

```text
button.*
old setup controls
old dashboard controls
old debug/control entities with previous names
old sensor/status entities
```

It does not remove the normal Home Assistant RFLink integration.



## Sidebar dashboard mode fix

Home Assistant YAML dashboard registration must use:

```yaml
lovelace:
  mode: storage
  dashboards:
    rflink-raw-tools:
      mode: yaml
      filename: rflink_raw_dashboard.yaml
      title: RFLink Raw Tools
      icon: mdi:radio-tower
      show_in_sidebar: true
      require_admin: false
```

Older RFLink Raw Tools builds wrote `resource_mode: storage`, which can pass config check but not register the sidebar dashboard correctly.

To fix an already-written block:

```bash
sh /config/fix-rflink-dashboard-mode.sh
ha core check
ha core restart
```

Or manually change this line in `/config/configuration.yaml`:

```yaml
resource_mode: storage
```

to:

```yaml
mode: storage
```

## Sidebar/dashboard behavior

The sidebar dashboard is YAML-registered. Turning the sidebar/dashboard switch on writes the managed dashboard block, but Home Assistant usually does not show a new YAML dashboard until after restart.

After turning on dashboard/sidebar:

```bash
ha core check
ha core restart
```

Then hard-refresh the browser.

If the sidebar remains after removing the dashboard, check:

```text
Settings -> Dashboards
```

If it is not removable there, check for the managed block in:

```text
/config/configuration.yaml
```

The managed block starts with:

```text
# BEGIN RFLink Raw Tools managed dashboard
```

and ends with:

```text
# END RFLink Raw Tools managed dashboard
```

## No-Press UI rule

Home Assistant native `ButtonEntity` controls render as **Press** on the device page. This project should not use `ButtonEntity` for the main UI.

This build has no `button.py` platform.

Main setup/undo controls are switches:

```text
RFLink Prerequisite   on = install, off = undo
RFLink Dashboard      on = add dashboard, off = undo dashboard
RFLink Sidebar        on = add to sidebar, off = remove from sidebar
```

One-time dashboard actions call services directly, so dashboard labels can say things like:

```text
Send raw
Send protocol
Ping
Version
Download latest
Reset UI
```

## Emergency undo

The package includes:

```text
undo-rflink-raw-tools.sh
```

The installer copies it to:

```text
/config/undo-rflink-raw-tools.sh
```

Run only if you need to disable/remove RFLink Raw Tools managed files:

```bash
sh /config/undo-rflink-raw-tools.sh
ha core restart
```

It backs up first, then removes managed RFLink Raw Tools YAML blocks/files and disables the integration folder.

## Troubleshooting

### `sh /config/reset-rflink-raw-ui.sh: python3: not found`

Use the Home Assistant service instead:

```text
Developer Tools -> Actions -> rflink_raw.reset_ui
```

Then:

```bash
ha core restart
```

### `ModuleNotFoundError: No module named custom_components.rflink_raw.text`

The installed package is incomplete or old. Reinstall:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ls -la /config/custom_components/rflink_raw/text.py /config/custom_components/rflink_raw/number.py
ha core restart
```

### Sidebar switch is on but no sidebar item appears

Restart Core:

```bash
ha core check
ha core restart
```

Then hard-refresh the browser.

### Duplicate RFLink Raw Tools entries

Keep one integration entry and delete the duplicate from:

```text
Settings -> Devices & services -> RFLink Raw Tools
```

Two devices are expected. Two integration entries are not.


## Dashboard entity-not-found fix

If the sidebar dashboard opens but shows **Entity not found**, the dashboard YAML has stale entity IDs.

Use:

```text
Developer Tools -> Actions -> rflink_raw.rebuild_dashboard
```

Then restart Home Assistant Core:

```bash
ha core restart
```

This build also rebuilds the dashboard automatically from the actual Home Assistant entity registry during integration setup. It does not assume fixed entity IDs.


## Dynamic dashboard optional-entity fix

The dashboard builder now treats these as optional and will not show a missing-entity warning for them:

```text
prereq_port
protocol_device_id
send_raw_command
send_protocol_command
update_from_github
restore_last_update
```

These are optional fields or service-call actions, not required dashboard entities.

To rebuild the dashboard:

```text
Developer Tools -> Actions -> rflink_raw.rebuild_dashboard
```

Then restart Home Assistant Core if the sidebar view does not refresh:

```bash
ha core restart
```


## Action and prerequisite fixes

### Ping / Version

The dashboard uses these services for gateway actions:

```text
rflink_raw.ping_gateway
rflink_raw.version_gateway
```

They send raw RFLink gateway commands and do not require `device_id`.

### Install RFLink prerequisite

The setup control is labeled:

```text
Install RFLink
```

If `configuration.yaml` already has a matching unmanaged `rflink:` block, RFLink Raw Tools now marks the prerequisite as satisfied instead of trying to write a duplicate block.

If `configuration.yaml` has a different unmanaged `rflink:` block, RFLink Raw Tools will not overwrite it.


## GUI update blocking-I/O fix

Older builds called `urllib.request.urlretrieve(...)` directly from an async Home Assistant action. Home Assistant blocks that because network I/O cannot run in the event loop.

This build keeps the version at `0.0.1` but changes update/restore actions to run through:

```text
hass.async_add_executor_job(...)
```

That means future GUI updates can use:

```text
RFLink Raw Tools sidebar -> Update -> Download latest
```

Because the currently installed updater is the broken one, install this fix once with the terminal installer after pushing it to GitHub:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```


## Install RFLink prerequisite detection

`Install RFLink` now treats any existing top-level `rflink:` block in `configuration.yaml` as satisfying the prerequisite.

That means:

- If your normal Home Assistant RFLink integration is already configured, the switch turns ON.
- RFLink Raw Tools does not write a duplicate `rflink:` block.
- Turning the switch OFF does not remove your user-managed `rflink:` block.
- The state is synced automatically during integration setup.

Example existing config that satisfies the prerequisite:

```yaml
rflink:
  port: /dev/ttyUSB0
  wait_for_ack: false
  reconnect_interval: 10
```
