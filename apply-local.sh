#!/bin/bash
set -euo pipefail

REPO="/Users/michaeldumas/Downloads/ha-rflink-raw-tools"
ZIP="/Users/michaeldumas/Downloads/ha-rflink-raw-tools-v0.1.0-stable-ui-onefile.zip"
EXTRACT="/Users/michaeldumas/Downloads/ha-rflink-raw-tools-stable-ui-extract"
BACKUP="/Users/michaeldumas/Downloads/ha-rflink-raw-tools-local-backup-$(date +%Y%m%d_%H%M%S)"

if [ ! -f "$ZIP" ]; then
  echo "ERROR: missing $ZIP"
  exit 1
fi

if [ ! -d "$REPO/.git" ]; then
  echo "ERROR: Git repo not found at $REPO"
  exit 1
fi

cp -R "$REPO" "$BACKUP"
rm -rf "$EXTRACT"
mkdir -p "$EXTRACT"
unzip -o "$ZIP" -d "$EXTRACT"

cd "$REPO"
rm -rf custom_components README.md LICENSE install.sh assets dashboard apply-local.sh
cp -R "$EXTRACT"/* .

chmod +x install.sh apply-local.sh

git add .
git commit -m "Stabilize UI, persist settings, and reduce admin controls" || true
git push --force-with-lease origin main

echo "Done. Backup saved to $BACKUP"
