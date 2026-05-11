#!/bin/sh
set -eu

APP="/config/custom_components/rflink_raw/www/rflink-raw-tools-panel.js"
CONST="/config/custom_components/rflink_raw/const.py"
COMP="/config/custom_components/rflink_raw"

echo "=== RFLink Raw Tools runtime check ==="
grep -n "APP_BUILD_ID" "$APP" || true
grep -n "PANEL_BUILD\|PANEL_MODULE" "$CONST" || true

echo ""
echo "Expected app build: install-gate-restart-fix-20260510"

echo ""
echo "Runtime Python cache note:"
echo "After ha core restart, Python may create __pycache__/*.pyc."
echo "That is normal runtime bytecode. It does NOT mean the package shipped stale files."

echo ""
echo "Current runtime cache files, if any:"
find "$COMP" -type d -name '__pycache__' -print
find "$COMP" -type f -name '*.pyc' -print

echo ""
echo "To verify install cleanliness before restart, run immediately after install and before ha core restart:"
echo "sh /config/check-rflink-before-restart.sh"
