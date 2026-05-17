# RFLink Raw Tools v0.0.2 Add-on Controls Package

This package keeps the previous Home Assistant add-on style and adds the missing software controls:

- Info / Configuration / Log top-level tabs
- Keeps RFLink Raw Tools in the sidebar by default
- Configuration controls for:
  - Install / repair RFLink YAML
  - Remove only the RFLink YAML block created by RFLink Raw Tools
  - Show / hide the RFLink Raw Tools sidebar app
  - Install / remove a reusable Home screen card snippet
  - Enable / disable alias-backed Home Assistant switch entities
- Log controls for:
  - Raw RF capture logging
  - Decoded RFLink logging
- Alias-backed Home Assistant switches from Teach/Alias records with ON and OFF commands
- HACS/GitHub release update path; no self-updater

Version: 0.0.2
Build: v002-addon-controls-20260517

## Apply in Home Assistant terminal

Upload or copy this package to `/config`, then run:

```sh
cd /config/rflink-v002-addon-controls-package
sh apply-rflink-v002-addon-controls.sh
ha core restart
```

After restart, hard refresh Chrome on Mac:

```text
Command + Shift + R
```

## Direct URL

The app remains available at:

```text
/rflink-raw-tools
```

## Safety note

The Remove RFLink YAML button only removes the YAML block created by RFLink Raw Tools. It refuses to delete a user-managed `rflink:` block.
