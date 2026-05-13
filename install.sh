#!/bin/sh
set -eu

REPO_ZIP_URL="https://github.com/michaeldn/ha-rflink-raw-tools/archive/refs/heads/main.zip"
TMP_ZIP="/tmp/ha-rflink-raw-tools.zip"
TMP_ROOT="/tmp/ha-rflink-raw-tools-install"
TMP_DIR="$TMP_ROOT/ha-rflink-raw-tools-main"
TARGET_DIR="/config/custom_components/rflink_raw"
BACKUP_DIR="/config/.rflink_raw_installer_backups/install_$(date +%Y%m%d_%H%M%S)"

fail() {
  echo ""
  echo "ERROR: $*" >&2
  echo "Home Assistant Core was NOT restarted." >&2
  exit 1
}

has_cache_artifacts() {
  DIR="$1"
  {
    find "$DIR" -type d -name '__pycache__' -print
    find "$DIR" -type f -name '*.pyc' -print
  } | grep -q .
}

print_cache_artifacts() {
  DIR="$1"
  {
    find "$DIR" -type d -name '__pycache__' -print
    find "$DIR" -type f -name '*.pyc' -print
  } || true
}

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
print_cache_artifacts "$TMP_DIR"

find "$TMP_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$TMP_DIR" -type f -name '*.pyc' -delete
find "$TMP_DIR" -type f -name '.DS_Store' -delete

echo ""
echo "=== Package cache check after cleanup ==="
if has_cache_artifacts "$TMP_DIR"; then
  print_cache_artifacts "$TMP_DIR"
  fail "Package still has __pycache__ or *.pyc after cleanup."
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
if ! sh /config/check-rflink-before-restart.sh; then
  fail "Installed target failed pre-restart check."
fi

echo ""
echo "All pre-restart checks passed."
echo "Backup saved to $BACKUP_DIR"
echo "Installed successfully."
echo "Home Assistant Core was NOT restarted by this installer to avoid SSH add-on/core_ssh restart noise."
echo "Restart Home Assistant Core manually from Settings -> System -> Restart Home Assistant."
