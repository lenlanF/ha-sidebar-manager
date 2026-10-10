# Changelog

## Unreleased — project foundation (2026-10-10)

- Established the HA Sidebar Manager project identity and roadmap.
- Recorded the upstream lineage and original MIT copyright notice.
- Defined compatibility-first migration and installation acceptance criteria.

**Not released:** No integration implementation has been imported, installed, or tested yet.


## Unreleased — compatibility branch (2026-10-10)

- Imported upstream panel framework and navigation shell.
- Updated OptionsFlow entry ownership and panel reload flow.
- Serialized shared static assets registration.
- Disabled the legacy unrestricted HTTP proxy at runtime.
- Added pre-release manifest and compatibility checklist.

**Not released:** work remains on the development branch; no Home Assistant runtime verification.


## Unreleased — flow and routing fixes (2026-10-10)

- New-entry UI now accepts the URL, icon, mode and administrator restriction in addition to title.
- Load legacy entry settings from the combined entry data/options map.
- Guard internal navigation during component updates rather than rendering.
- Add unexecuted validation regression tests.


## Unreleased — frontend modes and source checks (2026-10-10)

- Replaced legacy redirect shell with direct iframe handling.
- New-window mode uses an explicit link to avoid pop-up blockers.
- Added GitHub Actions syntax/JSON/source regression checks; outcomes not yet confirmed.


## Unreleased — visual manager, native CRUD and bootstrap

- Added administrator-only visual management panel and WebSocket API for native sidebar ConfigEntries.
- Added menu search, create/edit/delete, and management-list ordering controls.
- Added first-run manager-only setup without requiring a dummy menu shortcut.
- Added bilingual setup/option flows and legacy entry compatibility.
- Added isolated CRUD coverage plus HA Core API import smoke (Python 3.14 for HA 2026.10).
- Security: backend admin authorization and preserved disabling of unsafe wildcard HTTP proxy.

**Not released:** live HA browser tests, packaging validation, migration rehearsals, native per-user sidebar order, drag/drop and custom user permissions remain outstanding.


## Unreleased — UI compatibility and safety (2026-10-10)

- Replaced HA-internal Lit inheritance with standalone native custom elements for menu display.
- Removed unused legacy wildcard HTTP proxy and redirect shell.
- Added Node checks for internal navigation and URL/iframe mode behavior.
- Fixed a regression allowing removal of the manager bootstrap entry from the management API.
- Updated GitHub Actions and validated source + Core API import jobs successfully (run 38039794524).

## Unreleased — HA integration validation and HACS readiness (2026-10-10)

- Fixed deprecated config-entry unload callback invocation discovered by HA 2026.10 functional tests.
- Added real HA tests for manager setup, legacy entry reload, native menu setup, admin WebSocket CRUD, and non-admin access denial.
- Added integration branding PNG and official HACS repository validation.
- Updated minimum advertised Home Assistant support to 2026.10.0.
- HA 2026.10 functional suite 5/5 passed; HACS validation 8/9 passed (missing repository Topics setting).

**Not released:** browser/mobile and production upgrade validations are still required.

## Unreleased — 0.1.0-dev.2 development branch (2026-10-10)

- Clean up shared manager panel on final config entry unload; re-register panel safely on subsequent setup without duplicating WebSocket commands.
- Add visual enable/disable menu controls, preserving legacy entries and using native HA reloads.
- Add visual DOM regressions (create/edit/delete, error recovery, escaping, toggle).
- Expand functional HA Core tests to 7 passing tests. GitHub Actions run 38041489728.
- HACS Topics and actual production/browser acceptance remain unresolved; no release created.

## Unreleased — HACS and Chromium validation (2026-10-10)

- HACS repository validation now passes 9/9 following Topics configuration.
- Added Playwright desktop and mobile Chromium interaction tests; 2/2 passed using a mocked HA WebSocket backend.
- Source checks and Home Assistant Core functional suite (7/7) pass; run 38041795993.
- Production upgrade and true HA frontend browser acceptance remain release blockers.

## Unreleased — 0.1.0-dev.3 (2026-10-10)

- Add visual menu JSON export and preview-before-apply import; backend uses admin-only WebSocket and native ConfigEntry APIs.
- Add versioned backup format, validation/size limits, conflict checks, duplicate-safe imports and same-title legacy menu support.
- Preserve unrelated old options when restoring the supported menu fields; no auto-delete, no claims of atomic or full HA rollback.
- Add desktop/mobile Chromium export/restore scenarios and HA Core backup/migration/security tests.
- Verification: **12/12 HA Core functional tests**, **2/2 Chromium browser tests** and **HACS 9/9** on commit `8f3c0aa7a`.
- Full legacy HACS upgrade and real HA frontend testing remain release blockers.

## Unreleased — 0.1.0-dev.4 (2026-10-10)

- Added upstream 2026.4.13 configuration-layout compatibility fixture and real Core regression tests.
- Verified legacy HA OptionsFlow edit path and HA HTTP serving of manager/panel JavaScript resources.
- Fixed cross-instance menu restoration to update icon, permissions, enablement and order when title+URL matches.
- Verification: 16/16 HA 2026.10 Core tests and Chromium desktop/mobile tests passed (run 38050016651).
- HACS repository structure remains valid; live HACS source replacement, persistent restart and full frontend/Ingress test remain release blockers.

## Unreleased — 0.1.0-dev.5 (2026-10-10)

- Preserve previously unknown legacy OptionsFlow values when editing old menus; explicitly keep unsafe proxy disabled.
- Add safe round-trip backup restoration for original title-only sidebar entries without a configured URL.
- Add HA native storage serialization regression for preserving old data/options and updated menu settings.
- Verification: **19/19** HA 2026.10 Core tests, Chromium desktop/mobile, source/API checks and HACS **9/9** passed. No production upgrade or true process restart claimed.

## Unreleased — 0.1.0-dev.6 (2026-10-10)

- Add separate-process HA Core native ConfigEntry storage write/cold-load checks, preserving legacy entry IDs, unknown options and manager/menu states.
- Fix test harness double setup after automatic frontend loading; no integration defect established by that first test failure.
- CI includes dedicated cross-process storage check, all existing HA Core functional and Chromium UI checks; full source run 38054007697 succeeded.
- Official HACS validation 9/9 succeeded on source commit a574f6652.
- Full independent HA service restart and HACS upstream repo replacement remain untested; not released.

## Unreleased — 0.1.0-dev.7 (2026-10-10)

- Add source-swap migration rehearsal using the actual upstream panel_iframe 2026.4.13 Git commit, followed by fork loading and original-source rollback.
- Exercise all three phases in independent Python processes using Home Assistant's native ConfigEntry storage and original ConfigFlow.
- Document the upstream deprecated hot-reload caveat and test-harness timeout; do not claim full HACS migration or HA service restart.
- Automated checks passed: three pinned upgrade/rollback phases, 19 HA Core tests, Chromium UI, source/API tests, HACS validator 9/9 (run 38057571508 / 38057571332).

## Unreleased — 0.1.0-dev.8 (2026-10-10)

- Add desktop/mobile Chromium regression using actual HA Core HTTP server and authenticated browser-native WebSocket; create/edit/toggle/delete verify real ConfigEntry changes.
- Add test-only UTF-8 HTML hosted by HA; no WebSocket response mocks or browser local-network security bypass.
- All Source checks passed: 19 HA Core tests, genuine upstream upgrade/rollback, separate-process native storage load and 2/2 real Chromium WebSocket tests (https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38059902505). HACS validation 9/9 (https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38059902424).
- Full HA authenticated frontend shell, HACS installed source swap and Supervisor backup restore still remain pre-release blockers.

## Unreleased — 0.1.0-dev.9 (2026-10-10)

- Add real Chromium tests of HA Core's authenticated frontend `get_panels` registry, using both admin and read-only HA accounts.
- Validate correct frontend visibility, registered custom-panel names and modules, actual HA SPA index routing, menu link safety and prompt removal from panel metadata on unload.
- Verified 4/4 browser tests using real HA HTTP and WebSocket; 19 HA Core functional tests and all other CI checks passed (source run 38061488602); HACS 9/9 passed (run 38061488639).
- Still not a full signed-in HA frontend shell or actual HACS migration acceptance; no official release.

## Unreleased — 0.1.0-dev.10 (2026-10-11)

- Add two Chromium tests that boot the actual authenticated Home Assistant SPA at the manager route, exercising real UI composition and native WebSocket menu creation at desktop and mobile viewport widths.
- Fix isolated HA fixture onboarding initialization to prevent redirecting the browser to the first-run welcome screen.
- Verified **6/6 actual HA HTTP/WebSocket Chromium tests**, 19 HA Core functional tests, all 7 source CI jobs, and HACS repository validation 9/9.
- Remaining release gates: HACS-installed source migration, HAOS/Supervisor restart + backup restore, physical mobile and Ingress/CSP; no release.
