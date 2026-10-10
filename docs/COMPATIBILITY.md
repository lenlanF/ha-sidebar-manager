# Compatibility foundation (unreleased)

This branch is not a released HA integration. It imports the upstream text-based runtime, retains domain `panel_iframe`, and updates the options-flow access pattern to `self.config_entry`.

## Known gaps
- Upstream MDI font assets and preview page are not bundled yet (binary files cannot be imported by the current source-writing route).
- No live Home Assistant installation or integration tests have been performed.
- Legacy HTTP proxy is intentionally disabled: upstream registers an unrestricted router endpoint and requires a security redesign.
- Internal route navigation is still implemented in the upstream JS render method, pending rewrite.
- Entry creation and registration lifecycle still need full multi-entry regression testing.
- Visual management screen is not implemented.

## First checks before release
1. Import remaining runtime resources, verify HACS packaging.
2. Install in disposable supported Home Assistant, check logs.
3. Add/configure/reload/delete several entries; ensure no duplicate static route errors.
4. Verify old config entries and both mobile/desktop views.
5. Validate browser navigation, permissions, HTTP(S) iframe behavior.
