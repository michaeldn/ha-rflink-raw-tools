#!/bin/bash
set -euo pipefail

REPO="/Users/michaeldumas/Projects/ha-rflink-raw-tools"
ZIP="/Users/michaeldumas/Downloads/ha-rflink-raw-tools-v0.0.1-app-ws-debug-ux-fix-onefile.zip"
EXTRACT="/Users/michaeldumas/Downloads/ha-rflink-raw-tools-v0.0.1-app-ws-debug-ux-fix-extract"
BACKUP="/Users/michaeldumas/Downloads/ha-rflink-raw-tools-local-backup-$(date +%Y%m%d_%H%M%S)"

if [ ! -d "$REPO/.git" ]; then
  echo "Local repo not found: $REPO"
  exit 1
fi

rm -rf "$EXTRACT"
mkdir -p "$EXTRACT"
unzip -o "$ZIP" -d "$EXTRACT"

mkdir -p "$BACKUP"
cp -R "$REPO" "$BACKUP/repo"

cd "$REPO"

# Clean old generated/stale package artifacts but keep git.
find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +

cp -R "$EXTRACT"/. "$REPO"/

find "$REPO" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$REPO" -type f -name '*.pyc' -delete
find "$REPO" -type f -name '.DS_Store' -delete

python3 - <<'PY'
import py_compile
from pathlib import Path
errors = []
for p in Path("custom_components/rflink_raw").glob("*.py"):
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as e:
        errors.append((str(p), str(e)))
if errors:
    raise SystemExit(errors)
print("Python compile check passed.")
PY

git status --short
git add .
git commit -m "Fix RFLink app websocket status and debug switches" || true
git push origin main

echo "Done. Backup saved to $BACKUP"
