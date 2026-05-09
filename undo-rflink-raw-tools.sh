#!/bin/sh
    set -eu

    cd /config || exit 1

    TS="$(date +%Y%m%d_%H%M%S)"
    BACKUP="/config/rflink_raw_undo_backup_$TS"
    mkdir -p "$BACKUP"

    echo "Backing up before undo to: $BACKUP"

    cp configuration.yaml "$BACKUP/configuration.yaml" 2>/dev/null || true
    cp .storage/core.config_entries "$BACKUP/core.config_entries" 2>/dev/null || true
    cp .storage/core.device_registry "$BACKUP/core.device_registry" 2>/dev/null || true
    cp .storage/core.entity_registry "$BACKUP/core.entity_registry" 2>/dev/null || true
    cp .storage/lovelace_dashboards "$BACKUP/lovelace_dashboards" 2>/dev/null || true
    cp .storage/rflink_raw_tools_state "$BACKUP/rflink_raw_tools_state" 2>/dev/null || true

    echo "Removing managed YAML blocks from configuration.yaml..."
    sed -i '/# BEGIN RFLink Raw Tools managed dashboard/,/# END RFLink Raw Tools managed dashboard/d' configuration.yaml
    sed -i '/# BEGIN RFLink Raw Tools managed RFLink prerequisite/,/# END RFLink Raw Tools managed RFLink prerequisite/d' configuration.yaml

    echo "Removing RFLink Raw Tools dashboard/logo files..."
    rm -f rflink_raw_dashboard.yaml
    rm -rf www/rflink_raw

    echo "Disabling custom integration folder..."
    mkdir -p custom_components_disabled
    if [ -d custom_components/rflink_raw ]; then
      mv custom_components/rflink_raw "custom_components_disabled/rflink_raw_DISABLED_$TS"
    fi

    echo "Removing RFLink Raw Tools saved state..."
    rm -f .storage/rflink_raw_tools_state

    echo "Removing RFLink Raw Tools storage dashboards if present..."
    python3 - <<'PY'
import json
from pathlib import Path

base = Path("/config/.storage")
dash = base / "lovelace_dashboards"
if dash.exists():
    data = json.loads(dash.read_text())
    items = data.get("data", {}).get("items", [])
    kept = []
    removed = 0
    for item in items:
        text = json.dumps(item).lower()
        if "rflink raw tools" in text or "rflink-raw-tools" in text or "rflink_raw_dashboard" in text:
            removed += 1
        else:
            kept.append(item)
    data.setdefault("data", {})["items"] = kept
    dash.write_text(json.dumps(data, indent=2, sort_keys=True))
    print("Removed storage dashboard entries:", removed)

for p in base.glob("lovelace.rflink*"):
    print("Removing", p)
    p.unlink()
PY

    echo ""
    echo "Undo complete. Backup saved to: $BACKUP"
    echo "Run: ha core check"
    echo "Then restart Home Assistant Core."
