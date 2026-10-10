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
