#!/bin/sh
set -eu

REPO_ZIP_URL="https://github.com/michaeldn/ha-rflink-raw-tools/archive/refs/heads/main.zip"
TMP_ZIP="/tmp/ha-rflink-raw-tools.zip"
TMP_DIR="/tmp/ha-rflink-raw-tools-main"
TARGET_DIR="/config/custom_components/rflink_raw"
BACKUP_DIR="/config/.rflink_raw_installer_backups/install_$(date +%Y%m%d_%H%M%S)"

mkdir -p /config/custom_components "$BACKUP_DIR"

if [ -d "$TARGET_DIR" ]; then
  cp -R "$TARGET_DIR" "$BACKUP_DIR/rflink_raw"
fi

rm -f "$TMP_ZIP"
rm -rf "$TMP_DIR" "$TARGET_DIR"

wget -O "$TMP_ZIP" "$REPO_ZIP_URL"
unzip -o "$TMP_ZIP" -d /tmp

cp -R "$TMP_DIR/custom_components/rflink_raw" "$TARGET_DIR"

# Never leave compiled/cache artifacts behind.
find "$TARGET_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$TARGET_DIR" -type f -name '*.pyc' -delete

echo "Installed RFLink Raw Tools app baseline."
echo "Backup saved to $BACKUP_DIR"
echo "Restart Home Assistant Core: ha core restart"
