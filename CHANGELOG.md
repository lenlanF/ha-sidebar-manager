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
