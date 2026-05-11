#!/bin/sh
set -eu
APP="/config/custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
CONST="/config/custom_components/rflink_raw/const.py"
echo "=== RFLink Raw Tools frontend build ==="
grep -n "APP_BUILD_ID" "$APP" || true
grep -n "PANEL_BUILD\|PANEL_MODULE" "$CONST" || true
echo ""
echo "If the app screen does not show a Clear command button or Setup -> App build,"
echo "Chrome is still using an old cached module. Use Command + Shift + R."
