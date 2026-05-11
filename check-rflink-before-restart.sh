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
echo "Package/install cache artifacts before restart:"
CACHE_FOUND=0
if find "$TARGET" -type d -name '__pycache__' -print | grep -q .; then
  CACHE_FOUND=1
fi
if find "$TARGET" -type f -name '*.pyc' -print | grep -q .; then
  CACHE_FOUND=1
fi

if [ "$CACHE_FOUND" -eq 0 ]; then
  echo "PASS: no __pycache__ or *.pyc in installed target before restart."
else
  echo "FAIL: cache artifacts exist before restart."
  echo "Run: sh /config/clean-rflink-runtime-cache.sh"
  exit 2
fi

echo ""
echo "Important:"
echo "After ha core restart, Python may recreate __pycache__/*.pyc. That is normal runtime bytecode."
