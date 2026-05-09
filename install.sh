#!/bin/sh
set -eu

REPO_ZIP_URL="https://github.com/michaeldn/ha-rflink-raw-tools/archive/refs/heads/main.zip"
TMP_ZIP="/tmp/ha-rflink-raw-tools.zip"
TMP_DIR="/tmp/ha-rflink-raw-tools-main"
TARGET_DIR="/config/custom_components/rflink_raw"

echo "Installing RFLink Raw Tools from GitHub..."
mkdir -p /config/custom_components

rm -f "$TMP_ZIP"
rm -rf "$TMP_DIR"
rm -rf "$TARGET_DIR"

wget -O "$TMP_ZIP" "$REPO_ZIP_URL"
unzip -o "$TMP_ZIP" -d /tmp

cp -R "$TMP_DIR/custom_components/rflink_raw" "$TARGET_DIR"

echo "Installed to $TARGET_DIR"
echo "Restart Home Assistant Core next:"
echo "ha core restart"
