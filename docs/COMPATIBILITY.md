# Compatibility status — stable v0.1.0

The stable release retains upstream `panel_iframe` domain and native ConfigEntry storage. Full authenticated Home Assistant SPA + Chromium, real HA Core WebSocket, earlier source upgrade/rollback and HACS repository validation have passed in automation. Prior development milestone counts below are kept for history. Actual upstream-HACS source switching, Supervisor Ingress and full HAOS backup restore remain field validation items.

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

## Additional field acceptance following v0.1.0 release
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

## v0.1.0-dev.5 — old options and unconfigured entries

- Old `OptionsFlow` settings not recognized by this release are now preserved on native edits (tested), except legacy proxy activation is intentionally forced off.
- Historical title-only entries with no URL can be exported/imported through an explicitly guarded restore path; they are visible in manager lists as not configured but do not register clickable sidebar panels.
- Verified HA native `core.config_entries` serialized data with old extra fields and modified options intact after delayed save. This is a storage-layer regression, not a full HA process cold-start.
- HA 2026.10 Core integration **19/19 passed**, Chromium desktop/mobile and source checks succeeded on https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38053139374; HACS validation 9/9 on https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38053139396.

## v0.1.0-dev.6 — native storage across Python process boundaries

`tests/integration/test_restart_persistence.py` plus the `cross-process-config-reload` CI job write representative old-style ConfigEntries using Home Assistant Core and then load the serialized native storage envelope into a fresh HA Core ConfigEntries manager in **a different Python process**.

This verifies entry IDs, titles, legacy options, manager-only entry, blank-URL entries and enabled/disabled behavior with frontend registration. Verified by CI run https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38054007697 (both process stages passed; functional HA 19 passed), with HACS 9/9 in https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38054007745.

This deliberately does not claim complete HA service shutdown/startup in distinct processes, an actual HACS repository swap, or whole-server restore. These remain pre-release blockers.

## v0.1.0-dev.7 — pinned upstream source-swap exercise

CI downloads `shaonianzhentan/panel_iframe@90c849d34b3ebb749c5f62a3e206e62888e4c050` (v2026.4.13). Separate pytest/Python processes exercise authentic original ConfigFlow, HA native options persistence, a cold load into the fork, and a return to original files with the original ConfigEntry store. Three phases passed: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38057571508. This is substantially more grounded than a hand-authored legacy fixture.

**Not exercised**: original OptionsFlow's obsolete reload/UI path, actual HACS repository installation metadata, full HA service subprocess lifecycles, networked live-HA frontend and full Supervisor backup restore. Do not represent a source-copy test as a production HACS migration.

## v0.1.0-dev.8 — browser-native WebSocket connected to real HA

The `tests/live_browser` fixture runs the actual HA 2026.10 HTTP and WebSocket server and fetches the management JavaScript through HA HTTP. Playwright Chromium uses a browser-native authenticated WS connection; the UI's create/edit/enable/disable/delete operations mutate and verify actual HA ConfigEntries, on both 1366px and 375px viewports.

The HTML host is served by a **test-only HA HTTP static registration** from `tests/live_browser/host.html`. This avoids Chromium 153's Local Network Access rejection of synthetic Playwright-fulfilled pages without weakening Chromium security. It is still not the full logged-in HA frontend shell or mobile native app.

Evidence: 2/2 real browser WS scenarios + all previously implemented suites passed (https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38059902505); HACS 9/9 (https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38059902424). Full HACS-installed source replacement, Ingress, whole-HA restart and Supervisor restore remain untested.

## v0.1.0-dev.9 — real frontend registry, permissions and URL serving

Real Chromium tests against HA Core 2026.10 now cover the native frontend `get_panels` WebSocket command using administrator and read-only credentials, admin-only and unrestricted panel visibility, the module URLs registered in HA's frontend panel metadata, safe new-window links, and the real SPA index responder at manager/menu paths. Panel unload is verified against subsequent `get_panels` responses.

CI evidence: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38061488602 (4/4 browser tests, 19 HA Core functional tests, all jobs passing) and https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38061488639 (HACS 9/9). This still **does not** exercise full authenticated HA SPA shell rendering or an actual HACS installation-source change.

## v0.1.0-dev.10 — complete HA SPA boot

Two live Chromium checks now run the installed HA frontend itself at `/ha-sidebar-manager`, with ephemeral test authentication and finalized onboarding state. Both desktop and mobile viewports rendered `ha-sidebar-manager-panel` via the HA frontend panel registry, obtained real `hass.connection`, and created a native ConfigEntry. Together with the four real HA HTTP/WS minimal-host tests, all **6/6 passed** in https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38068306091. HACS official repository checks **9/9** passed in https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38068306086.

Still unverified: HACS repository source switching, true HAOS/Supervisor reboot, whole-system backup restore, physical phones, ingress/CSP and remote iframe policies.

## v0.1.0-dev.11 — iframe safety, CSP/XFO and internal route

Real Chromium ran the iframe mode 0/1 matrix against a genuine HA HTTP-served host and panel script. The allowed target was served directly by HA; X-Frame-Options DENY and CSP frame-ancestors none were injected only into disposable test iframe responses to avoid HA's HTTP middleware replacing headers. Chromium enforced the browser rules while visible safe new-window links remained available. This is not a Supervisor Ingress test or a policy bypass.

The full authenticated HA SPA mode-3 test navigated to the integrations view. HA 2026.10 canonicalizes /config/integrations to /config/integrations/dashboard; the assertion now accepts this valid destination. Run https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38069857572: 12/12 live HA/Chromium, 19 Core functional tests, all CI jobs success. HACS 9/9: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38069857573. Real HAOS/Supervisor Ingress remains untested.
