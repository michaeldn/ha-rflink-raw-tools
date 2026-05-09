# RFLink Raw Tools

<p align="center"><img src="assets/logo.png" alt="RFLink Raw Tools" width="220"></p>

RFLink Raw Tools is a Home Assistant custom integration that adds a cleaner RFLink control UI, RFDEBUG/QRFDEBUG helpers, repeat controls, GitHub updating, and dashboard/sidebar setup.

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

## Default device page cleanup

The Home Assistant device page cannot be fully redesigned by a custom integration. Home Assistant controls that layout.

This release reduces the mess on that page by marking most setup fields as configuration entities and most status/log/help items as diagnostic entities. The main user experience should be the sidebar dashboard, while the device page should now be treated as an admin/config page.

The clean daily-use UI is the sidebar dashboard:

```text
RFLink Raw Tools
```

## Why this exists

The default Home Assistant device page lists every entity in one long view. That is why it can look like a CVS receipt.

RFLink Raw Tools uses a dedicated dashboard as the primary user-facing page instead:

```text
Start
Setup
Control
Debug
Update
```

## Dashboard yes/no / sidebar yes/no

RFLink Raw Tools can register the bundled dashboard automatically.

It writes a managed Lovelace dashboard block like this:

```yaml
lovelace:
  resource_mode: storage
  dashboards:
    rflink-raw-tools:
      mode: yaml
      filename: rflink_raw_dashboard.yaml
      title: RFLink Raw Tools
      icon: mdi:radio-tower
      show_in_sidebar: true
      require_admin: false
```

If `show_in_sidebar` is on, Home Assistant shows **RFLink Raw Tools** in the left sidebar.

Home Assistant supports multiple dashboards, each dashboard can be added to the sidebar, and YAML dashboards are defined under `lovelace.dashboards` with options including `filename`, `title`, `icon`, and `show_in_sidebar`.

## Prerequisite

The normal Home Assistant RFLink integration must already be working before RFLink Raw Tools can send RFLink commands.

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

## Update from the UI

After the first install, open:

```text
Settings → Devices & services → Devices → RFLink Raw Tools
```

Press:

```text
Update Download Latest From GitHub
```

Then restart Home Assistant Core from the UI.

## Important limitation

This integration sends RFLink gateway text commands.

It does not make classic RFLink R48 replay arbitrary `DEBUG;Pulses=...` captures unless the RFLink firmware itself supports a transmit command for that format.
