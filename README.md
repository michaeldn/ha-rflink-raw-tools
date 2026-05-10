# RFLink Raw Tools

<p align="center"><img src="assets/logo.png" alt="RFLink Raw Tools" width="120"></p>

Version: **0.0.1**

## UI reset program

This build prevents the update problem where old Home Assistant entities stay behind after the integration changes.

It includes three reset paths:

1. Automatic cleanup on integration setup.
2. A Home Assistant service:

   ```text
   rflink_raw.reset_ui
   ```

3. A terminal script copied to `/config` by `install.sh`:

   ```bash
   sh /config/reset-rflink-raw-ui.sh
   ha core restart
   ```

The reset removes stale RFLink Raw Tools entities from old builds, especially old `button.*` entities that showed the unwanted native **Press** CTA.

## No-Press UI

Home Assistant's native `ButtonEntity` renders as **Press** on the device page. This build has no `button.py` platform.

- Setup/undo controls are switches.
- Dashboard one-time actions call services directly.
- Version remains `0.0.1`.

## Install

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

## Manual UI reset after update

```bash
sh /config/reset-rflink-raw-ui.sh
ha core restart
```
