#!/bin/sh
set -eu

cat <<'TXT'
RFLink Raw Tools app baseline installed.

If setup failed earlier with:
  ValueError: Overwriting panel rflink-raw-tools

This build fixes that by removing any existing RFLink Raw Tools panel before registering it again.

After install:
  ha core restart

Then check:
  Settings -> Devices & services -> RFLink Raw Tools

Keep one integration entry only. If there are duplicates, delete the extra entry.

HACS note:
  This repository is HACS-ready because it includes hacs.json and the custom_components/rflink_raw structure.
  To actually use HACS, add the GitHub repository in HACS as a custom integration repository.
TXT
