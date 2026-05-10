#!/bin/sh
set -eu

DASH="/config/rflink_raw_dashboard.yaml"

if [ ! -f "$DASH" ]; then
  echo "Dashboard file not found: $DASH"
  exit 1
fi

echo "RFLink Raw Tools send actions in dashboard:"
grep -n "send_saved\|send_stored" "$DASH" || true

if grep -q "rflink_raw.send_stored_raw\|rflink_raw.send_stored_protocol" "$DASH"; then
  echo ""
  echo "Old send_stored service names are still in the dashboard."
  echo "Run Developer Tools -> Actions -> rflink_raw.rebuild_dashboard, then restart Core if needed."
  exit 2
fi

echo ""
echo "Dashboard is using the new send_saved service names."
