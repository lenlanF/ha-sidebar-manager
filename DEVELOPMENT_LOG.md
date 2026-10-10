# Development Log

## 2026-10-10 — Repository initialization

- Target repository: https://github.com/lenlanF/ha-sidebar-manager
- Upstream: https://github.com/shaonianzhentan/panel_iframe
- Upstream inspected: `config_flow.py`, `__init__.py`, `manifest.py`, `www/panel_iframe.js`, `manifest.json`, `hacs.json`, `LICENSE`.
- Confirmed upstream integration domain: `panel_iframe`, upstream manifest version: `2026.4.13`.
- Identified migration and API review areas: `OptionsFlow` initialization and `config_entry` access, static resource registration across multiple entries, panel register/unregister and update listener lifecycle, frontend render-time redirects, unsafe HTTP proxy access.
- Initial repository state: empty; authenticated GitHub integration reports push permission.
- Completed: created project identity, roadmap, copyright notice and logs.
- Tests: none (documentation-only initialization).
- Release/package: none. Do not install this repository through HACS yet.
- Next: import all upstream code and resource files without omissions, establish regression tests; then repair config flow and multi-entry registration before beginning new UI work.

## Acceptance criteria — first code milestone

1. A new sidebar item can be added, edited and removed on supported HA versions.
2. Existing `panel_iframe` entries retain titles, URLs and display mode after an upgrade.
3. Multiple entries and reloads do not raise route-already-registered errors.
4. Internal HA URLs navigate correctly, without recurring navigation side effects from `render()`.
5. Logs and tests demonstrate compatibility; failures are visible, not swallowed.


## 2026-10-10 — Compatibility foundation work (dev/compat-foundation)

- Imported upstream integration Python runtime, frontend script, HTML shell and existing translation into a dedicated development branch.
- Added an unreleased HA integration manifest and HACS metadata.
- Changed options flow initialization to use Home Assistant supplied `self.config_entry` rather than manually retaining an older entry object.
- Reworked shared static-path registration behind an async lock to avoid repeated registration from multiple entries.
- Replaced manual unload/sleep/re-setup update path with native config-entry reload.
- Disabled invocation of the upstream wildcard HTTP proxy pending a security review; legacy option values are retained.
- Outstanding: MDI binary assets, multi-entry live tests, internal-route redirect rewrite, visual manager UI, security review, package validation.
- Verification: GitHub writes confirmed; **no HA runtime test or distributable package yet**.
- Do not merge or release until the prerequisites in `docs/COMPATIBILITY.md` are verified.


## 2026-10-10 — Complete initial-entry form and route lifecycle

- New config entry flow now collects title, target URL, MDI icon, display mode, administrator flag in one step. It validates empty values and internal paths; implicit proxy is disabled.
- Existing entries use combined data + options, preserving historical titles and old options.
- Frontend internal routing no longer mutates history from render(); navigation is guarded in updated().
- Added config validation test specifications (not executed yet).
- Source files re-fetched after writes for review.
- **Unverified:** HA runtime, browser integration, CI, HACS packaging, binary MDI assets, proxy security rewrite, visual management UI.
- Next: make a real, installable test candidate; run HA integration and browser tests; fix discovered errors before merging to main.


## 2026-10-10 — Frontend opening-mode hardening & CI

- Replaced legacy nested HTML redirect approach with direct iframe rendering in the compatibility web component.
- New-tab mode now presents a user-initiated link (no unsolicited window.open calls); HTTP iframe targets in HTTPS instances are presented as external links.
- Internal-route navigation remains in updated() rather than render(); mode 3 rejects non-relative URLs.
- Added CI source checks: Python compilation, JSON parsing, node JS syntax check, isolated validation regression tests.
- Added an isolated test module that extracts the pure validator with AST; **does not substitute for live Home Assistant config flow tests**.
- No HA runtime verification has been performed and no GitHub Actions result has been inspected.
- Known blockers: real HA testing, add-on support validation, manager visual UI, migration and permissions, leftover old web assets and dependency cleanup. No HACS release.


## 2026-10-10 — Visual management UI and native CRUD

- Added `custom_components/panel_iframe/manager_api.py` with administrator-only WebSocket list/save/delete/reorder commands. Saves use HA ConfigEntry APIs, not an additional database.
- Added `www/manager.js`, a mobile-responsive management page with menu search, add/edit/delete, icon, title, URL, mode and administrator-visibility controls.
- Registered one shared `/ha-sidebar-manager` admin panel, alongside original `panel_iframe` item panels.
- Integrated existing legacy ConfigEntry records via combined `data` and `options` values.
- Changed setup flow: first install can create `manager_only` bootstrap config entry without a dummy sidebar shortcut. Manager bootstrap entries are excluded from CRUD list and protected from deletion by management WebSocket methods.
- Added simplified Chinese and English setup and option translations.
- Recorded that management list sorting is separate from HA native per-user sidebar ordering; drag/drop, groups and custom user visibility are **not implemented**.
- Added isolated WebSocket CRUD tests covering legacy configs, admin decorators, invalid delete/reorder and manager entry protection.
- CI: `Source checks` succeeded on source branch through `bdc06152...`, run https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38039492747
- CI: Home Assistant Core API import smoke first failed because Python 3.13 cannot install HA 2026.10 (requires Python >=3.14.2). Corrected to Python 3.14 and subsequently passed, https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38039393859
- The CI checks do **not** exercise a running HA frontend or real ConfigEntry persistence. No HACS release, production installation, or migration was performed.
- Next: run complete test instance with multiple legacy entries, add/edit/delete and reload; verify mobile frontend, paths and CSP; prepare safe backup/rollback and HACS validation before merging.


## 2026-10-10 — Frontend independence, dead-code removal, and regression fix

- Rewrote legacy menu display web component as a native HTMLElement. It no longer waits for the lazily loaded `ha-panel-lovelace` Lit component.
- Preserved four display modes, internal route navigation, explicit new-window links, and invalid-URL protections.
- Removed obsolete `http_proxy.py` and unused `www/index.html` redirect shell. The unsafe proxy is not registered.
- Added a dependency-free Node regression to verify internal navigation executes once, external URLs cannot be internal-route targets, and iframe/new-tab modes behave as intended.
- Added bootstrap manager test which discovered a real defect: the deletion endpoint did not guard `manager_only` entries. Fixed deletion authorization on that entry and reran tests.
- Updated Actions versions and added run concurrency to stop duplicate work.
- Verified run **38039794524** at https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38039794524: `syntax-and-tests` = success; `homeassistant-api-smoke` = success.
- Still not verified: installing/operating against a real HA browser and full ConfigEntry runtime, upgrade migration, HACS package or user-level permissions. Keep this work on development branch until those gates pass.

## 2026-10-10 — HA 2026.10 functional acceptance and HACS validation

- Added integration test fixtures that copy `panel_iframe` into a disposable HA config directory and install the exact frontend dependency used by HA 2026.10.
- Fixed a real compatibility defect exposed by tests: `ConfigEntry.async_unload_callbacks()` no longer exists; Home Assistant performs `async_on_unload` callbacks itself.
- Tested real HA config flows, first-install manager bootstrap, legacy multi-entry setup and reloading, CRUD via authenticated WebSocket, and read-only user's access denial.
- Evidence: **5 Home Assistant Core functional tests passed**, plus separate syntax/isolated checks and HA API import smoke; https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38040925266
- Added `custom_components/panel_iframe/brand/icon.png` to satisfy HACS integration branding.
- HACS action: 8 of 9 checks passed after brand addition; only GitHub repository Topics missing (repository setting; code cannot supply it). Evidence: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38040715657
- Updated HACS minimum supported HA to 2026.10.0, the only HA release tested with functional checks.
- CI environment corrections: Python 3.14 required, install `home-assistant-frontend==20260930.2`, provide an OAuth client ID for the test read-only user.
- **Not yet verified:** browser rendering of manager UI, end-to-end HACS install in an actual user HA environment, real backup and rollback over installed upstream HACS integration, mobile Ingress and CSP behavior.
- No merge to main; no release or deployment.

## 2026-10-10 — Manager lifecycle, toggles and UI DOM regression (v0.1.0-dev.2)

- Reviewed repository docs and all major menu modules before modification.
- Fixed shared manager panel lifecycle: unload removes each entry panel, and after the final loaded entry unregisters the shared manager panel while keeping WebSocket commands registered exactly once for future setup.
- Added HA Core regression for multiple entries, last-entry unload and subsequent manager re-setup.
- Added an `enabled` menu option (defaults to true for existing `panel_iframe` entries): supports toggling from the manager list and native HA config/options form without deleting the underlying entry.
- Menu registration now respects `enabled=False`, and update listeners reload panel registrations accordingly.
- Added DOM tests with jsdom for creating/editing/deleting, save-failure draft retention, HTML escaping and enable/disable controls. These are simulated DOM checks, **not** complete HA browser UI tests.
- Automated check evidence: [GitHub Actions run 38041489728](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38041489728): `syntax-and-tests` success, `homeassistant-api-smoke` success, `homeassistant-functional-tests` success; functional suite **7/7 passed**.
- HACS structural check remains 8/9 until repository Topics are added. The connected GitHub tool has repository file write access but does not expose a Topics update method.
- Not verified: production upgrade and rollback; native HACS install lifecycle; desktop/mobile browser rendering and iframe/Ingress compatibility.
- Version advanced to `0.1.0-dev.2` for the **unreleased development branch** only. Main and releases remain unchanged.

## 2026-10-10 — HACS 9/9 and Chromium responsive UI checks

- GitHub repository Topics are now configured (`hacs`, `home-assistant`, `homeassistant`, `sidebar`, `smart-home`); verified using GitHub API readback. **Topics were not written through the GitHub connector, which does not expose a topics-update action.**
- Official HACS validation passed **9/9**: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38041489760
- Added Playwright Chromium browser UI checks at desktop 1366×768 and mobile 375×812. Both cover add/edit/delete, enable/disable, and horizontal overflow of forms/buttons/cards with a mocked HA WebSocket backend.
- First browser test failure was an ambiguous test locator matching both the status toast and menu badge; fixed the locator to target the badge. No application code change was needed for this failure.
- Latest completed complete source run: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38041795993 — Chromium **2/2**, HA Core functional **7/7**, isolated/source checks and API import all passed.
- Not yet done: browser tests connected to an actual Home Assistant frontend/backend, end-to-end HACS install, old HACS integration upgrade migration/rollback, Ingress/CSP checks and per-user visibility beyond the native administrator restriction.
- No main-branch merge or release performed.

## 2026-10-10 — Menu snapshot, safe restore preview and legacy migration coverage (v0.1.0-dev.3)

- Added `custom_components/panel_iframe/backup.py`: versioned, size-bounded menu snapshot and full-file preflight planner, retaining supported legacy item configuration without using HA private .storage internals.
- Added administrator-only `panel_iframe/manager/backup` and `panel_iframe/manager/restore` WebSocket endpoints. Import defaults to dry-run; explicit apply is required. Existing entries match by ConfigEntry ID; new entries use HA's native config flow. There is no implicit delete of menus absent from the snapshot.
- Added local JSON download, file upload, preview counts and explicit confirmation in the visual manager. URL details may be sensitive; browser downloads should be stored securely.
- Preserved extra legacy data/options on existing entry updates, disabled old insecure proxy settings, and ensured backed-up unknown metadata is not misrepresented as restorable to a different HA instance.
- Added safety limits: 100 menus, 256 KB JSON, validated title/path/icon/mode/order/booleans, duplicate target checks and conflicting-name protection.
- Fixed an edge case for two distinct legacy menus having the same display title: preserve their separate ConfigEntry identities and URLs; do not collapse or reject them.
- Added HA Core integration tests: export/preview/apply/skip; cross-instance missing-entry creation; malformed/conflicting snapshot rejection before any writes; non-admin access denial; old same-title entries recovery.
- Extended Playwright Chromium desktop/mobile tests to download JSON, change existing menu settings, preview import without mutations, then confirm restoration. Added isolated Python backup planner tests for hostile formats and legacy duplicate names.
- **Confirmed on commit `8f3c0aa7a`**: HA 2026.10 Core functional tests **12/12 passed**, Chromium manager tests **2/2 passed**, isolated tests and HA API import smoke passed: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38043711432.
- **Confirmed HACS 9/9 passed** on same code: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38043711445.
- Added `docs/UPGRADE_AND_ROLLBACK.md` with disposable-instance migration procedure and mandatory full HA backup. Menu-level restore is explicitly **non-atomic** and not a full HA software rollback.
- Outstanding: actual upgrade of an already HACS-installed original `panel_iframe` in a disposable HA system, full live-HA frontend browsing, Ingress/CSP matrix, and production rollback rehearsals. **No main merge or release**.

## 2026-10-10 — Verify original 2026.4.13 entry layout and HA HTTP resources (v0.1.0-dev.4)

- Fetched and reviewed actual upstream `shaonianzhentan/panel_iframe` code at version 2026.4.13. Verified `ConfigFlow` creates entries with `data={"title":...}`, and `OptionsFlow` writes `icon`, `url`, `mode`, `require_admin`, and `proxy_access` into options.
- Added a **sanitized representative upstream entry fixture**, `tests/fixtures/upstream_2026_4_13.json` (not a user backup, not actual HACS-installed state), and real HA Core regression verifying old entries load, original `data`/`options` survive, entries appear in manager list, and proxy settings are not executed. Legacy proxy is disabled intentionally; opening modes relying on it may behave differently.
- Added native HA OptionsFlow migration test against old-style entries to ensure users can edit old shortcuts without recreating them, while preserving unknown legacy data.
- Fixed cross-instance backup restoration: an entry matching title + URL now restores differing icon, admin restriction, enablement and order instead of being incorrectly skipped. Added HA Core integration regression for this behavior.
- Added HA HTTP smoke test that fetches `manager.js` and `panel_iframe.js` via registered static paths, detecting missing runtime frontend assets.
- Evidence: [GitHub Actions source checks](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38050016651) **16/16 actual HA 2026.10 Core tests passed**, Chromium desktop/mobile test jobs passed, API import and isolated/source checks passed.
- Evidence: [HACS official validation](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38050016667) passed for code prior to this documentation/version bump; current development-branch version remains unreleased.
- Not yet completed: real *in-place* upstream HACS repository swap, saved HA configuration across a process restart, browser using real HA frontend + WebSocket, Ingress restrictions, and verified full backup rollback.
- No main merge and no GitHub Release. Resume real-source migration rehearsal before any release.

## 2026-10-10 — Legacy data preservation, unconfigured menu restore, native storage (v0.1.0-dev.5)

- Reviewed code and logs at v0.1.0-dev.4; discovered old-style OptionsFlow was replacing the entire options mapping, silently dropping unknown upstream options on edit. Fixed by merging old options with validated new values, while keeping the deprecated unsafe `proxy_access` explicitly disabled.
- Added regression assertion that a legacy custom `old_option` survives native HA OptionsFlow edit, not only its `data` fields.
- Identified a second data-loss case: the upstream plugin allows creating a title-only ConfigEntry before URL configuration; its menu backup could export the record, but restore rejected the empty URL. Added an explicit, restore-only `restore_unconfigured` path, allowing old URL-less entries to round-trip without appearing as clickable sidebar items. Normal menu creation still requires URL.
- Extended backup preflight to accept blank URL placeholders only in restore context, while preserving normal URL validation and admin-only WebSocket authorization.
- Added live HA Core tests for URL-less legacy entry JSON round-trip into a new ConfigEntry, its native OptionsFlow, and preserving old options.
- Added HA native configuration storage regression using `hass_storage` and `freezer` to verify serialized `core.config_entries` retains title, entry ID, legacy `data` and `options`, and updated menu settings after the HA save delay. This is **not** proof of a complete independent HA process restart.
- Evidence: `Source checks` https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38053139374 — HA 2026.10 Core **19/19 passed**, source/isolated checks and Chromium desktop/mobile browser jobs passed, and HA API smoke passed.
- Evidence: HACS official validator https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38053139396 — **9/9 passed**.
- Still pending: real upstream HACS in-place repository replacement with full config backup/rollback, full HA process restart in a separate environment, and Chromium UI connected to the real HA frontend/Ingress. No production deployment, main merge or official Release.

## 2026-10-10 — Cross-process ConfigEntry cold-load regression (v0.1.0-dev.6)

- Re-read previous project log, current version, CI and HA 2026.10 ConfigEntries storage/load implementation before changes.
- Added `tests/integration/test_restart_persistence.py` in two explicitly separate pytest/Python process phases. Phase A sets up representative legacy entries, modifies their native options, waits for HA store saving, and serializes the HA storage envelope to a disposable JSON file in the CI runner.
- Phase B is a different Python process. It reads the artifact, initializes a fresh HA `ConfigEntries` manager through HA's native Store loader, verifies stable entry IDs, original `data`/unknown `options` fields, manager-only entry, title-only placeholder, and enabled/disabled setting. It also validates that the manager panel loads while disabled/unconfigured menu panels do not appear.
- Added a dedicated `cross-process-config-reload` GitHub Actions job with distinct Process A and Process B commands, on HA 2026.10 and Python 3.14.
- First run **failed because the test called async_setup twice** after HA automatically loaded entries when frontend was set up; this was a test harness error, not lost data. Fixed by checking `ConfigEntryState` and invoking setup only for entries still NOT_LOADED.
- Passing final result on source commit `a574f6652`: [GitHub Actions](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38054007697) — **cross-process write 1 passed / read 1 passed** (the nonselected phase intentionally skipped in each subprocess), HA Core functional **19 passed / 2 phase-skipped**, Chromium UI, isolated/source and HA API smoke jobs passed.
- Official HACS validator: **9/9 passed** on the same source commit, [run](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38054007745).
- **Boundary:** this is an isolated two-Python-process HA Core store cold-load test with a serialized on-disk artifact. It does **not** launch the full HA service in separate OS processes, does not replace an actually installed upstream HACS repository, and does not verify a HA Supervisor backup/restore. Keep original-upstream HACS source swap, full service reboot and production rollback on the release blocker list.
- No code merge into main, no HACS release, no production change.
