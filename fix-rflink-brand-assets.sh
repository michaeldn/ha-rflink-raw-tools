#!/bin/sh
set -eu

BRAND_DIR="/config/custom_components/rflink_raw/brand"
COMP_DIR="/config/custom_components/rflink_raw"
WWW_DIR="/config/www/rflink_raw"

mkdir -p "$BRAND_DIR" "$WWW_DIR"

if [ ! -f "$BRAND_DIR/icon.png" ] || [ ! -f "$BRAND_DIR/logo.png" ]; then
  echo "Brand files are missing from $BRAND_DIR."
  echo "Re-run the installer after pushing the latest package."
  exit 1
fi

cp "$BRAND_DIR/icon.png" "$BRAND_DIR/dark_icon.png"
cp "$BRAND_DIR/icon.png" "$BRAND_DIR/icon@2x.png"
cp "$BRAND_DIR/icon.png" "$BRAND_DIR/dark_icon@2x.png"
cp "$BRAND_DIR/logo.png" "$BRAND_DIR/dark_logo.png"
cp "$BRAND_DIR/logo.png" "$BRAND_DIR/logo@2x.png"
cp "$BRAND_DIR/logo.png" "$BRAND_DIR/dark_logo@2x.png"

cp "$BRAND_DIR/icon.png" "$COMP_DIR/icon.png"
cp "$BRAND_DIR/logo.png" "$COMP_DIR/logo.png"
cp "$BRAND_DIR/logo.png" "$WWW_DIR/logo.png"

echo "RFLink Raw Tools brand files verified:"
ls -la "$BRAND_DIR"/icon.png "$BRAND_DIR"/logo.png "$BRAND_DIR"/dark_icon.png "$BRAND_DIR"/dark_logo.png "$BRAND_DIR"/icon@2x.png "$BRAND_DIR"/logo@2x.png

echo ""
echo "Expected approved hashes:"
echo "  logo.png md5: 16bad0221d68821784cd5d26a33f2d3c"
echo "  icon.png md5: 07429242aaec19f7a5c2d031535255ff"
echo ""
echo "Run: ha core restart"
