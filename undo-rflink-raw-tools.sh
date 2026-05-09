#!/bin/sh
set -eu

cd /config || exit 1
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/config/rflink_raw_undo_backup_$TS"
mkdir -p "$BACKUP"

cp configuration.yaml "$BACKUP/configuration.yaml" 2>/dev/null || true
cp .storage/core.config_entries "$BACKUP/core.config_entries" 2>/dev/null || true
cp .storage/core.device_registry "$BACKUP/core.device_registry" 2>/dev/null || true
cp .storage/core.entity_registry "$BACKUP/core.entity_registry" 2>/dev/null || true
cp .storage/lovelace_dashboards "$BACKUP/lovelace_dashboards" 2>/dev/null || true
cp .storage/rflink_raw_tools_state "$BACKUP/rflink_raw_tools_state" 2>/dev/null || true

sed -i '/# BEGIN RFLink Raw Tools managed dashboard/,/# END RFLink Raw Tools managed dashboard/d' configuration.yaml
sed -i '/# BEGIN RFLink Raw Tools managed RFLink prerequisite/,/# END RFLink Raw Tools managed RFLink prerequisite/d' configuration.yaml

rm -f rflink_raw_dashboard.yaml
rm -rf www/rflink_raw
rm -f .storage/rflink_raw_tools_state

mkdir -p custom_components_disabled
if [ -d custom_components/rflink_raw ]; then
  mv custom_components/rflink_raw "custom_components_disabled/rflink_raw_DISABLED_$TS"
fi

echo "Undo complete. Backup saved to $BACKUP"
echo "Run: ha core check"
