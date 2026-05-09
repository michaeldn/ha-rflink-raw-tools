# RFLink Raw Tools

<p align="center"><img src="assets/logo.png" alt="RFLink Raw Tools" width="220"></p>

RFLink Raw Tools is a Home Assistant custom integration that adds a **Devices & services UI** for RFLink gateway commands.

It now also includes:

- a bundled **logo**
- clearer button labels that say what to press and what happens next
- built-in **Help** buttons for logs, device finding, and dashboard setup
- a cleaner optional **second page** dashboard YAML
- a GUI helper to install the normal Home Assistant RFLink prerequisite YAML

## Linux / Home Assistant OS install

Open the Home Assistant Terminal and run:

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

After Home Assistant restarts, add the integration:

```text
Settings → Devices & services → Add integration → RFLink Raw Tools
```

## Integration icon / logo

RFLink Raw Tools includes Home Assistant local brand assets in:

```text
custom_components/rflink_raw/brand/
```

Included files:

```text
icon.png
dark_icon.png
logo.png
dark_logo.png
```

Home Assistant 2026.3 and later can load custom integration brand images directly from the integration `brand/` folder. After updating, restart Home Assistant Core and hard refresh the browser if the old placeholder icon is still cached.

## What improved in the UI

The default device page is organized by prefixes so it is easier to scan:

- **Setup ...**
- **Control ...**
- **Debug ...**
- **Help ...**
- **Status ...**

Buttons are clearer now. For example, instead of vague actions, you now get labels like:

- **Help Show Log Commands**
- **Help Show Find Device Steps**
- **Help Load Example Raw Command**
- **Control Send RFLink Raw Command**
- **Setup Install RFLink Prerequisite YAML**

The Help buttons open persistent notifications inside Home Assistant with the next step to take.

## Cleaner second page dashboard

This package installs:

- `/config/www/rflink_raw/logo.png`
- `/config/rflink_raw_dashboard.yaml`

Use that YAML file to create a dedicated RFLink Raw Tools dashboard page in Home Assistant.

Go to:

```text
Settings → Dashboards
```

and create/import a dashboard using `/config/rflink_raw_dashboard.yaml`.

That second page is cleaner than the default device page and uses the bundled logo.

## Update from the UI

After the first install, non-technical users do not need to update from the command line.

Open:

```text
Settings → Devices & services → Devices → RFLink Raw Tools
```

Press:

```text
Update Download Latest From GitHub
```

Then restart Home Assistant Core from the UI:

```text
Settings → System → Restart Home Assistant
```

The update button downloads the public GitHub `main` branch, copies the integration into `/config/custom_components/rflink_raw`, refreshes the bundled logo/dashboard files, and saves a backup in:

```text
/config/.rflink_raw_backups
```

The only command-line step is the first install, because Home Assistant custom integrations cannot install themselves before they exist.

## How to Run

Open the created device:

```text
Settings → Devices & services → Devices → RFLink Raw Tools
```

Recommended flow:

1. Press **Setup Load Default Prerequisite Values** if needed.
2. Press **Setup Install RFLink Prerequisite YAML**.
3. Run `ha core check` and restart Home Assistant.
4. Use **Control ...** entities/buttons to send commands.
5. Use **Debug ...** entities/buttons to capture RF activity.
6. Use **Help ...** buttons any time you need instructions.

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

## Manual install

Copy `custom_components/rflink_raw` to `/config/custom_components/rflink_raw` and then restart Home Assistant.

## Important limitation

This integration sends RFLink gateway text commands.

It does **not** make classic RFLink R48 replay arbitrary `DEBUG;Pulses=...` captures unless the RFLink firmware itself supports a transmit command for that format.
