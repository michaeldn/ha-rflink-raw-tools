#!/bin/sh
set -eu

cd /config || exit 1

TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/config/rflink_raw_ui_reset_backup_$TS"
mkdir -p "$BACKUP"

cp .storage/core.entity_registry "$BACKUP/core.entity_registry" 2>/dev/null || true
cp .storage/core.device_registry "$BACKUP/core.device_registry" 2>/dev/null || true

PY_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PY_BIN="python"
fi

if [ -z "$PY_BIN" ]; then
  echo "Python is not available in this Terminal add-on container."
  echo ""
  echo "Use the built-in Home Assistant reset service instead:"
  echo "  Developer Tools -> Actions -> RFLink Raw Tools: Reset RFLink Raw Tools UI"
  echo "  Service name: rflink_raw.reset_ui"
  echo ""
  echo "Then restart Home Assistant Core:"
  echo "  ha core restart"
  echo ""
  echo "Backup saved to $BACKUP"
  exit 2
fi

"$PY_BIN" - <<'PY'
import json
from pathlib import Path

ENTITY_KEEP = {
    "switch.rflink_prerequisite",
    "switch.rflink_dashboard",
    "switch.rflink_sidebar",
    "switch.rflink_prerequisite_wait_for_ack",
    "text.rflink_prerequisite_port",
    "number.rflink_prerequisite_reconnect_interval",
    "switch.send_rflink_raw_command",
    "switch.send_rflink_protocol_command",
    "switch.rflink_qrfdebug",
    "switch.rflink_rfdebug",
    "switch.rflink_ping",
    "switch.rflink_version",
    "text.rflink_raw_command",
    "text.rflink_protocol_device_id",
    "text.rflink_protocol_command",
    "number.rflink_repeat_count",
    "number.rflink_repeat_delay",
    "switch.update_download_latest_from_github",
    "switch.undo_last_github_update",
}

entity_path = Path("/config/.storage/core.entity_registry")
removed_entities = []

if entity_path.exists():
    data = json.loads(entity_path.read_text())
    entities = data.get("data", {}).get("entities", [])
    kept = []

    for entity in entities:
        platform = entity.get("platform")
        entity_id = entity.get("entity_id", "")

        if platform == "rflink_raw" and entity_id not in ENTITY_KEEP:
            removed_entities.append(entity_id)
        else:
            kept.append(entity)

    data["data"]["entities"] = kept
    entity_path.write_text(json.dumps(data, indent=2, sort_keys=True))

print("Removed stale RFLink Raw Tools entities:", len(removed_entities))
for entity_id in removed_entities:
    print(" -", entity_id)
PY

echo "Backup saved to $BACKUP"
echo "Restart Home Assistant Core after this:"
echo "ha core restart"
