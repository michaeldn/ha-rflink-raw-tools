#!/bin/sh
    set -eu

    cd /config || exit 1
    TS="$(date +%Y%m%d_%H%M%S)"
    BACKUP="/config/rflink_raw_stale_entity_backup_$TS"
    mkdir -p "$BACKUP"

    cp .storage/core.entity_registry "$BACKUP/core.entity_registry" 2>/dev/null || true

    python3 - <<'PY'
import json
from pathlib import Path

p = Path("/config/.storage/core.entity_registry")
if not p.exists():
    print("No entity registry found.")
    raise SystemExit(0)

data = json.loads(p.read_text())
entities = data.get("data", {}).get("entities", [])

kept = []
removed = []
for e in entities:
    eid = e.get("entity_id", "")
    platform = e.get("platform", "")
    # This build has no RFLink Raw Tools ButtonEntity platform.
    if platform == "rflink_raw" and eid.startswith("button."):
        removed.append(eid)
    else:
        kept.append(e)

data["data"]["entities"] = kept
p.write_text(json.dumps(data, indent=2, sort_keys=True))
print("Removed stale RFLink Raw Tools button entities:", len(removed))
for eid in removed:
    print(" -", eid)
PY

    echo "Backup saved to $BACKUP"
    echo "Restart HA Core after running this."
