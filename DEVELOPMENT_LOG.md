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
