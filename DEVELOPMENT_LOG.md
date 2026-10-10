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
