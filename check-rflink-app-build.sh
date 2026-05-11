#!/bin/sh
set -eu

APP="/config/custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
CONST="/config/custom_components/rflink_raw/const.py"
COMP="/config/custom_components/rflink_raw"

echo "=== RFLink Raw Tools frontend build ==="
grep -n "APP_BUILD_ID" "$APP" || true
grep -n "PANEL_BUILD\|PANEL_MODULE" "$CONST" || true

echo ""
echo "Expected app build: runtime-cache-check-fix-20260510"

echo ""
echo "=== Runtime Python cache note ==="
echo "Home Assistant/Python may create __pycache__/*.pyc after restart."
echo "That is normal runtime bytecode, not proof the package zip shipped stale files."

echo ""
echo "Current runtime cache files, if any:"
find "$COMP" -type d -name '__pycache__' -print
find "$COMP" -type f -name '*.pyc' -print

echo ""
echo "Optional cleanup while HA is running:"
echo "find /config/custom_components/rflink_raw -type d -name '__pycache__' -prune -exec rm -rf {} +"
echo "find /config/custom_components/rflink_raw -type f -name '*.pyc' -delete"
echo ""
echo "They may return after another Core restart. That is expected."
