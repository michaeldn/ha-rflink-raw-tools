#!/bin/sh
set -eu

TARGET="/config/custom_components/rflink_raw"

echo "Cleaning runtime Python cache under $TARGET"
find "$TARGET" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$TARGET" -type f -name '*.pyc' -delete
echo "Done."

echo ""
echo "Note: Home Assistant/Python may recreate __pycache__ after import/restart. That is normal."
