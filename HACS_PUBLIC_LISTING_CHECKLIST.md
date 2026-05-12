# HACS Public Listing Checklist

This repository is prepared for HACS validation. These steps still need to be completed in GitHub / external repos before it can appear in the public HACS default search.

## Repository settings

Set the GitHub repository description to:

```text
Home Assistant sidebar tool for RFLink capture, setup checks, and sending learned 433 MHz RFLink commands.
```

Add GitHub topics:

```text
home-assistant
hacs
hacs-integration
rflink
433mhz
rf
homeassistant
custom-component
```

Enable GitHub Issues.

## Required validation

Actions added in this package:

```text
.github/workflows/hacs.yml
.github/workflows/hassfest.yml
.github/workflows/static-package.yml
```

All should pass before requesting inclusion.

## Release

Create a GitHub release:

```text
Tag: v0.0.1
Title: RFLink Raw Tools v0.0.1
Body: paste RELEASE_NOTES_v0.0.1.md
```

## Brands

HACS public validation may require the integration to be present in `home-assistant/brands`.

Prepare a brands PR for:

```text
custom_integrations/rflink_raw/icon.png
custom_integrations/rflink_raw/logo.png
```

Use the approved artwork from:

```text
custom_components/rflink_raw/brand/icon.png
custom_components/rflink_raw/brand/logo.png
```

## HACS default inclusion

After the above passes, submit the repository to `hacs/default`.


## CI note

The repository workflow `Validate HACS` currently ignores these checks so the repo can have green CI before external setup is complete:

```text
brands description topics
```

Before submitting to `hacs/default`, remove the `ignore:` line from `.github/workflows/hacs.yml` and make sure it passes without ignores. HACS default inclusion requires the HACS Action and Hassfest to pass before submission.

## HACS manifest schema

Do not add `domains` to `hacs.json`; HACS rejects it as an unsupported key. The integration domain is declared in `custom_components/rflink_raw/manifest.json`.
