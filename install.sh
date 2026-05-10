#!/bin/sh
set -eu

REPO_ZIP_URL="https://github.com/michaeldn/ha-rflink-raw-tools/archive/refs/heads/main.zip"
TMP_ZIP="/tmp/ha-rflink-raw-tools.zip"
TMP_DIR="/tmp/ha-rflink-raw-tools-main"
TARGET_DIR="/config/custom_components/rflink_raw"
WWW_DIR="/config/www/rflink_raw"
DASHBOARD_FILE="/config/rflink_raw_dashboard.yaml"
BACKUP_DIR="/config/.rflink_raw_installer_backups/install_$(date +%Y%m%d_%H%M%S)"

mkdir -p /config/custom_components "$WWW_DIR" "$BACKUP_DIR"

if [ -d "$TARGET_DIR" ]; then
  cp -R "$TARGET_DIR" "$BACKUP_DIR/rflink_raw"
fi
if [ -f "$DASHBOARD_FILE" ]; then
  cp "$DASHBOARD_FILE" "$BACKUP_DIR/rflink_raw_dashboard.yaml"
fi
for script in /config/repair-stale-rflink-raw-entities.sh /config/reset-rflink-raw-ui.sh /config/undo-rflink-raw-tools.sh; do
  if [ -f "$script" ]; then
    cp "$script" "$BACKUP_DIR/"
  fi
done

rm -f "$TMP_ZIP"
rm -rf "$TMP_DIR" "$TARGET_DIR"

wget -O "$TMP_ZIP" "$REPO_ZIP_URL"
unzip -o "$TMP_ZIP" -d /tmp

cp -R "$TMP_DIR/custom_components/rflink_raw" "$TARGET_DIR"

if [ -f "$TMP_DIR/assets/logo.png" ]; then
  cp "$TMP_DIR/assets/logo.png" "$WWW_DIR/logo.png"
fi
if [ -f "$TMP_DIR/dashboard/rflink_raw_dashboard.yaml" ]; then
  cp "$TMP_DIR/dashboard/rflink_raw_dashboard.yaml" "$DASHBOARD_FILE"
fi
for script_name in repair-stale-rflink-raw-entities.sh reset-rflink-raw-ui.sh undo-rflink-raw-tools.sh; do
  if [ -f "$TMP_DIR/$script_name" ]; then
    cp "$TMP_DIR/$script_name" "/config/$script_name"
    chmod +x "/config/$script_name"
  fi
done

echo "Installed RFLink Raw Tools."
echo "Backup saved to $BACKUP_DIR"
echo "Restart Home Assistant Core: ha core restart"
