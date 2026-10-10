# Compatibility status (unreleased)

The development branch retains the upstream domain `panel_iframe` and ConfigEntry storage. It includes an administrator management panel and backend WebSocket handlers, and has passed seven real HA 2026.10 Core config-entry/WebSocket tests plus desktop/mobile Chromium tests with a simulated backend. Full live-HA browser acceptance remains outstanding.

## Checks implemented
- Chromium browser UI tests with simulated HA WebSocket backend: 1366px desktop and 375px mobile; both passed in run 38041795993. This is not a live-HA browser integration test.
- Functional suite against Home Assistant Core 2026.10 (7 passed): bootstrap, legacy multi-entry reload, native new-entry config flow, authenticated WebSocket CRUD, non-admin access denial. Run 38041795993.
- HACS validator 9/9 passed after the repository Topics were populated. Run 38041489760.
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

## v0.1.0-dev.3 migration-specific checks

- Versioned menu JSON backup, dry-run import and explicit apply; all commands are HA-admin only.
- Non-destructive preflight, conflict rejection, size and count restrictions, different-host menu creation and same-title legacy entry preservation.
- Confirmed on HA 2026.10 Core: 12/12 functional tests passed (run 38043711432).
- Chromium desktop/mobile UI (simulated HA backend): JSON export/download, import preview, confirmation and menu state recovery (2/2, same run).
- HACS repository validator: 9/9 passed (run 38043711445).
- Real HA frontend and upstream HACS in-place migration are **not** validated. A menu JSON is not an HA snapshot and importing it cannot reverse installed code upgrades.

## Upstream 2026.4.13 migration fixture / v0.1.0-dev.4

Upstream ConfigFlow saves the menu title inside `ConfigEntry.data`. Its OptionsFlow saves `icon`, `url`, `mode`, `require_admin`, and `proxy_access` in `options`. A sanitized representative fixture in `tests/fixtures/upstream_2026_4_13.json` covers this layout. It is not an extracted HA user backup.

The real HA 2026.10 test suite verifies loading old entries, native options editing, preserving unknown legacy fields, cross-instance restoration of icon/permissions/state/order and serving frontend JavaScript through real HA HTTP. Run https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38050016651: 16/16 passed.

Legacy HTTP proxy behavior is intentionally **disabled** and will not be restored automatically; users depending on it must migrate to a supported secure URL/open method. An actual HACS repository source swap over installed upstream code, persistent HA process restart, and production rollback are still untested.
