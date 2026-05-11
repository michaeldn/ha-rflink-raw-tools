#!/bin/sh
set -eu
APP="/config/custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
CONST="/config/custom_components/rflink_raw/const.py"
echo "=== RFLink Raw Tools frontend build ==="
grep -n "APP_BUILD_ID" "$APP" || true
grep -n "PANEL_BUILD\|PANEL_MODULE" "$CONST" || true
echo ""
echo "=== Cache artifacts check ==="
find /config/custom_components/rflink_raw -type d -name '__pycache__' -print
find /config/custom_components/rflink_raw -type f -name '*.pyc' -print
echo ""
echo "Nothing should print under Cache artifacts check."

echo "Expected app build: debug-status-ux-fix-20260510"
