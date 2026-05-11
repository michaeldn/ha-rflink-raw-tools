#!/bin/bash
set -euo pipefail

REPO="/Users/michaeldumas/Projects/ha-rflink-raw-tools"
ZIP="/Users/michaeldumas/Downloads/ha-rflink-raw-tools-v0.0.1-pre-restart-check-fix-onefile.zip"
EXTRACT="/Users/michaeldumas/Downloads/ha-rflink-raw-tools-v0.0.1-pre-restart-check-fix-extract"
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

git rm -r --cached --ignore-unmatch custom_components/rflink_raw/__pycache__ >/dev/null 2>&1 || true
find "$REPO" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$REPO" -type f -name '*.pyc' -delete
find "$REPO" -type f -name '.DS_Store' -delete

find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
cp -R "$EXTRACT"/. "$REPO"/

find "$REPO" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$REPO" -type f -name '*.pyc' -delete
find "$REPO" -type f -name '.DS_Store' -delete

python3 - <<'PY'
import py_compile, shutil
from pathlib import Path

errors = []
for p in Path("custom_components/rflink_raw").glob("*.py"):
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as e:
        errors.append((str(p), str(e)))

for p in list(Path(".").rglob("__pycache__")):
    shutil.rmtree(p)
for p in list(Path(".").rglob("*.pyc")):
    p.unlink()

if errors:
    raise SystemExit(errors)
if list(Path(".").rglob("__pycache__")) or list(Path(".").rglob("*.pyc")):
    raise SystemExit("Cache artifacts still present")
print("Python compile and pre-commit no-cache checks passed.")
PY

git status --short
git add -A
git commit -m "Add RFLink pre-restart install cleanliness check" || true
git push origin main

echo "Done. Backup saved to $BACKUP"
