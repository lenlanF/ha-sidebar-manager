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
