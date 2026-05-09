# RFLink Raw Tools

<p align="center"><img src="assets/logo.png" alt="RFLink Raw Tools" width="120"></p>

Version: **0.0.1**

## No-Press UI build

Home Assistant's native `ButtonEntity` renders with a **Press** CTA on the device page. This build removes the ButtonEntity platform entirely.

- Setup/undo controls are on/off switches.
- Turning `RFLink Prerequisite` on installs the managed RFLink block.
- Turning `RFLink Prerequisite` off removes only that managed block.
- Turning `RFLink Dashboard` on adds the dashboard.
- Turning `RFLink Dashboard` off removes the managed dashboard.
- Dashboard one-time actions call services directly, so the dashboard can show clear CTAs like `Send raw`, `Ping`, and `Download latest`.
- Version remains `0.0.1`.

## Install

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

## Remove stale old button entities

Prior builds created RFLink Raw Tools button entities. This build has no button platform, so after installing run:

```bash
sh /config/repair-stale-rflink-raw-entities.sh
ha core restart
```
