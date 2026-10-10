# Compatibility status (unreleased)

The development branch retains the upstream domain `panel_iframe` and ConfigEntry storage. It includes an administrator management panel and backend WebSocket handlers, and has passed five real HA 2026.10 Core config-entry/WebSocket tests, but **not** browser acceptance tests.

## Checks implemented
- Functional suite against Home Assistant Core 2026.10 (5 passed): bootstrap, legacy multi-entry reload, native new-entry config flow, authenticated WebSocket CRUD, non-admin access denial. Run 38040925266.
- HACS validator 8/9 passed; repository Topics remains owner-setting blocker. Run 38040715657.
- Python compilation, JSON parsing, JavaScript syntax.
- Isolated validator and WebSocket CRUD regressions (with HA fakes).
- Python import and command decorator smoke against installable Home Assistant Core in GitHub Actions. This is **not** full HA runtime verification.

## Core integration decisions
- Upstream `panel_iframe` entries are displayed in the same management list as new menu entries.
- A new manager bootstrap entry uses `{"manager_only": true}`; it does not create its own menu shortcut in the managed list.
- Shared assets and admin manager panel are guarded by per-instance async locks.
- All writes use HA config flows / `hass.config_entries.async_update_entry` / `async_remove`.
- Legacy proxy access is not executed. Do not expose HTTP proxy routes without authentication and SSRF review.
- Management list order is not claimed to force every user's native sidebar order.
- The old MDI font preview assets are not present; the new manager UI uses HA's `ha-icon`.

## Blockers before official release
1. Test in a disposable Home Assistant 2026.10 installation and verify a clean log.
2. Install as upgrade over original `panel_iframe` with multiple configured entries. Verify title, URL and mode.
3. Confirm management panel and WebSocket CRUD in browser, including restart and reload persistence.
4. Verify all four open modes on desktop and mobile (ingress and CSP/X-Frame-Options cases).
5. Verify permission isolation for non-admin users and test the disabled legacy proxy is unreachable.
6. Add visible rollback/backup workflow and finish HACS packaging checks.
7. Add UI-based per-user visibility only with backend-enforced access controls.

See DEVELOPMENT_LOG.md for executed checks and run URLs.
