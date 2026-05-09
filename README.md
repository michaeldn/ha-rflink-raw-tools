# RFLink Raw Tools

<p align="center"><img src="assets/logo.png" alt="RFLink Raw Tools" width="220"></p>

RFLink Raw Tools is a Home Assistant custom integration for RFLink command sending, RFDEBUG/QRFDEBUG, dashboard/sidebar setup, and UI-based updates.

## What changed in this build

- The main RFLink Raw Tools device page is now only an admin landing page.
- The only enabled admin controls are:
  - Open RFLink Tools Dashboard
  - Add Dashboard
  - Add To Sidebar
- Command controls are moved to a separate device named RFLink Raw Tools Command Center.
- Status/log sensors are diagnostic and disabled by default to stop activity/log clutter.
- Settings are persisted in Home Assistant storage instead of being wiped on restart/update.

## Clean old test entities

Earlier test builds created many duplicate entities. Delete and re-add the integration once:

```text
Settings → Devices & services → RFLink Raw Tools → three dots → Delete
Restart Home Assistant
Settings → Devices & services → Add integration → RFLink Raw Tools
```

## First install

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

Then add the integration and keep:

```text
Install prerequisite: yes
Install dashboard: yes
Dashboard Show In Sidebar: yes
Dashboard Require Admin: no
```

Then:

```bash
ha core check
ha core restart
```

Use the RFLink Raw Tools item in the left sidebar as the primary UI.
