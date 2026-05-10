#!/bin/sh
set -eu

cd /config || exit 1

TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/config/rflink_raw_dashboard_mode_fix_backup_$TS"
mkdir -p "$BACKUP"

cp configuration.yaml "$BACKUP/configuration.yaml" 2>/dev/null || true

if grep -q "resource_mode: storage" configuration.yaml; then
  sed -i 's/^  resource_mode: storage$/  mode: storage/' configuration.yaml
  echo "Fixed dashboard registration: resource_mode -> mode"
else
  echo "No resource_mode dashboard line found. Nothing changed."
fi

echo "Backup saved to $BACKUP"
echo "Run:"
echo "  ha core check"
echo "  ha core restart"
