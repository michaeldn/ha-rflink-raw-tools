#!/bin/sh
set -eu

REPO_ZIP_URL="https://github.com/michaeldn/ha-rflink-raw-tools/archive/refs/heads/main.zip"
TMP_ZIP="/tmp/ha-rflink-raw-tools.zip"
TMP_DIR="/tmp/ha-rflink-raw-tools-main"
TARGET_DIR="/config/custom_components/rflink_raw"
WWW_DIR="/config/www/rflink_raw"
DASHBOARD_FILE="/config/rflink_raw_dashboard.yaml"

echo "Installing RFLink Raw Tools from GitHub..."
mkdir -p /config/custom_components
mkdir -p "$WWW_DIR"

rm -f "$TMP_ZIP"
rm -rf "$TMP_DIR"
rm -rf "$TARGET_DIR"

wget -O "$TMP_ZIP" "$REPO_ZIP_URL"
unzip -o "$TMP_ZIP" -d /tmp

cp -R "$TMP_DIR/custom_components/rflink_raw" "$TARGET_DIR"

if [ -f "$TMP_DIR/assets/logo.png" ]; then
  cp "$TMP_DIR/assets/logo.png" "$WWW_DIR/logo.png"
fi

if [ -f "$TMP_DIR/dashboard/rflink_raw_dashboard.yaml" ]; then
  cp "$TMP_DIR/dashboard/rflink_raw_dashboard.yaml" "$DASHBOARD_FILE"
fi

echo "Installed to $TARGET_DIR"
echo "Logo copied to $WWW_DIR/logo.png"
echo "Dashboard YAML copied to $DASHBOARD_FILE"
echo "Restart Home Assistant Core next:"
echo "ha core restart"
