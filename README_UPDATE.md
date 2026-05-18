# RFLink Raw Tools v0.0.2 Configuration / Overview / HACS icon fix

This package keeps the Info / Configuration / Log UI and fixes the Configuration page layout, Overview dashboard add/remove handling, and icon asset paths.

If Home Assistant's default Overview dashboard is still automatic and not storage-backed, RFLink Raw Tools cannot safely inject a card without taking over the user's dashboard. In that case it writes `/config/rflink_raw_home_card.yaml` as a fallback and says so explicitly.

HACS shows repository README/icon data from GitHub/HACS cache, not files pulled locally with wget. Commit the root `icon.png`, `logo.png`, `assets/icon.png`, `assets/logo.png`, and update the README/release before judging the HACS listing icon.
