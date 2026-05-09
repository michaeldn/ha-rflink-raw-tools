# RFLink Raw Tools

<p align="center"><img src="assets/logo.png" alt="RFLink Raw Tools" width="120"></p>

Version: **0.0.1**

## UI reset

- The dashboard logo is small.
- `Install RFLink Prerequisite` is a button, not a switch.
- `Install RFLink Prerequisite` is only available when the managed prerequisite block is not installed.
- `Undo RFLink Prerequisite` is available only after it is installed.
- Dashboard actions are also button pairs: Add / Undo and Add to sidebar / Remove from sidebar.
- The gear/configure page has no install actions.

## Install

```bash
wget -O - https://raw.githubusercontent.com/michaeldn/ha-rflink-raw-tools/main/install.sh | sh
ha core restart
```

## Stale entity repair

If old switches or old buttons from prior builds still show, copy/run:

```bash
sh /config/repair-stale-rflink-raw-entities.sh
```

Then restart Home Assistant Core.
