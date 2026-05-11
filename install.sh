#!/bin/sh
set -eu

REPO_ZIP_URL="https://github.com/michaeldn/ha-rflink-raw-tools/archive/refs/heads/main.zip"
TMP_ZIP="/tmp/ha-rflink-raw-tools.zip"
TMP_ROOT="/tmp/ha-rflink-raw-tools-install"
TMP_DIR="$TMP_ROOT/ha-rflink-raw-tools-main"
TARGET_DIR="/config/custom_components/rflink_raw"
BACKUP_DIR="/config/.rflink_raw_installer_backups/install_$(date +%Y%m%d_%H%M%S)"

mkdir -p /config/custom_components "$BACKUP_DIR"

if [ -d "$TARGET_DIR" ]; then
  cp -R "$TARGET_DIR" "$BACKUP_DIR/rflink_raw"
fi

rm -f "$TMP_ZIP"
rm -rf "$TMP_ROOT"
mkdir -p "$TMP_ROOT"

wget -O "$TMP_ZIP" "$REPO_ZIP_URL"
unzip -o "$TMP_ZIP" -d "$TMP_ROOT"

echo ""
echo "=== Package cache check before cleanup ==="
find "$TMP_DIR" -type d -name '__pycache__' -print || true
find "$TMP_DIR" -type f -name '*.pyc' -print || true

find "$TMP_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$TMP_DIR" -type f -name '*.pyc' -delete
find "$TMP_DIR" -type f -name '.DS_Store' -delete

echo ""
echo "=== Package cache check after cleanup ==="
if find "$TMP_DIR" -type d -name '__pycache__' -print | grep -q .; then
  echo "FAIL: package still has __pycache__ after cleanup"
  exit 2
fi
if find "$TMP_DIR" -type f -name '*.pyc' -print | grep -q .; then
  echo "FAIL: package still has *.pyc after cleanup"
  exit 2
fi
echo "PASS: package source is clean before install copy."

rm -rf "$TARGET_DIR"
cp -R "$TMP_DIR/custom_components/rflink_raw" "$TARGET_DIR"

find "$TARGET_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$TARGET_DIR" -type f -name '*.pyc' -delete
find "$TARGET_DIR" -type f -name '.DS_Store' -delete

for SCRIPT in check-rflink-app-build.sh check-rflink-before-restart.sh clean-rflink-runtime-cache.sh; do
  if [ -f "$TMP_DIR/$SCRIPT" ]; then
    cp "$TMP_DIR/$SCRIPT" "/config/$SCRIPT"
    chmod +x "/config/$SCRIPT"
  fi
done

echo ""
echo "=== Installed target pre-restart check ==="
sh /config/check-rflink-before-restart.sh

echo ""
echo "Installed RFLink Raw Tools app baseline."
echo "Backup saved to $BACKUP_DIR"
echo "Restart Home Assistant Core: ha core restart"
