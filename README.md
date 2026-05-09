# RFLink Raw Tools

<p align="center"><img src="assets/logo.png" alt="RFLink Raw Tools" width="220"></p>

RFLink Raw Tools is a Home Assistant custom integration that adds a cleaner RFLink control UI, RFDEBUG/QRFDEBUG helpers, repeat controls, GitHub updating, and dashboard/sidebar setup.

## Important: clean up old test entities

If you installed earlier test builds, Home Assistant may keep old entity names in the entity registry. That is why you may still see duplicate controls like both `RFLink Ping` and `Debug RFLink Ping`.

After installing this build, remove and re-add the integration once:

```text
Settings → Devices & services → RFLink Raw Tools → three dots → Delete
Restart Home Assistant
Settings → Devices & services → Add integration → RFLink Raw Tools
```

Then enable:

```text
Install dashboard: yes
Dashboard Show In Sidebar: yes
```

The default Home Assistant device page is now treated as an admin/config page. The primary daily UI is the sidebar dashboard.

## First install

Open the Home Assistant Terminal and run:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

Then go to:

```text
Settings → Devices & services → Add integration → RFLink Raw Tools
```

During setup, leave these enabled unless you already configured them yourself:

```text
Install prerequisite: yes
Install dashboard: yes
Dashboard Show In Sidebar: yes
Dashboard Require Admin: no
```

After setup:

```bash
ha core check
ha core restart
```

The clean RFLink Raw Tools dashboard should then appear in the left sidebar.

## Why this exists

The default Home Assistant device page lists enabled entities in Home Assistant's own layout. This integration keeps that page for admin/config and uses a dedicated dashboard as the main user page:

```text
Start
Setup
Control
Debug
Update
```

## Update from the UI

After the first install, open the RFLink Raw Tools device and press:

```text
Update Download Latest From GitHub
```

Then restart Home Assistant Core.

## Important limitation

This integration sends RFLink gateway text commands.

It does not make classic RFLink R48 replay arbitrary `DEBUG;Pulses=...` captures unless the RFLink firmware itself supports a transmit command for that format.
