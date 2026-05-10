#!/bin/sh
set -eu

cat <<'TXT'
RFLink Raw Tools post-update cleanup:

1. Restart Home Assistant Core:
   ha core restart

2. In Home Assistant:
   Developer Tools -> Actions -> rflink_raw.reset_ui
   Developer Tools -> Actions -> rflink_raw.rebuild_dashboard

3. Restart again if needed:
   ha core restart

4. If the integration still shows stale/missing entities or wrong device structure:
   Settings -> Devices & services -> RFLink Raw Tools -> three dots -> Delete
   Then add RFLink Raw Tools again.

This is sometimes necessary after platform/entity structure changes because Home Assistant may keep old registry/config-entry state.
TXT
