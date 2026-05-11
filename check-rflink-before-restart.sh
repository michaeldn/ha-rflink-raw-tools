#!/bin/sh
set -eu

TARGET="/config/custom_components/rflink_raw"
APP="$TARGET/www/rflink-raw-tools-panel.js"
CONST="$TARGET/const.py"

echo "=== RFLink Raw Tools pre-restart install check ==="
echo "This check is meant to run immediately after install and BEFORE ha core restart."

echo ""
echo "Frontend build:"
grep -n "APP_BUILD_ID" "$APP" || true
grep -n "PANEL_BUILD\|PANEL_MODULE" "$CONST" || true

echo ""
echo "Installed target cache artifacts before restart:"
CACHE_OUTPUT="$(
  {
    find "$TARGET" -type d -name '__pycache__' -print
    find "$TARGET" -type f -name '*.pyc' -print
  } || true
)"

if echo "$CACHE_OUTPUT" | grep -q .; then
  echo "$CACHE_OUTPUT"
  echo ""
  echo "FAIL: cache artifacts exist before restart."
  exit 2
fi

echo "PASS: no __pycache__ or *.pyc in installed target before restart."

echo ""
echo "Important:"
echo "After ha core restart, Python may recreate __pycache__/*.pyc. That is normal runtime bytecode."
