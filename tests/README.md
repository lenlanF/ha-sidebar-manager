# Testing tiers

**Executed in GitHub Actions (see DEVELOPMENT_LOG.md for exact run IDs):**
- Python syntax compilation, JSON parsing, JavaScript syntax.
- Isolated `tests/test_validation_isolated.py` and `tests/test_manager_isolated.py` with fake Home Assistant objects.
- Core import smoke on a Home Assistant-compatible Python interpreter.
- Five real Home Assistant 2026.10 Core integration tests using disposable config: bootstrap, legacy reload/unload, new entry, WebSocket CRUD and non-admin denial. Run 38040925266.

**Not yet executed:**
- End-to-end manual install and upgrade in a separate HA instance (functional fixture setup is already tested).
- Browser/mobile UI tests, Ingress routing, permissions and CSP/iframe behavior.
- Upgrade-over-legacy and rollback testing.

Isolated tests are deliberately not labeled as full integration tests.

- Added a seventh real Core functional test for enabled/disabled sidebar registration and manager lifecycle after final entry unload.
- Added jsdom-based manager UI create/edit/delete/toggle/error-handling checks. This is a simulated DOM test, not HA browser acceptance.
- Evidence: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38041489728 (7 functional tests passed).

- Headless Chromium UI checks (simulated HA backend): `npm install --no-save @playwright/test@1.55.1 && npx playwright install chromium && npx playwright test tests/browser/manager.spec.js --reporter=line`. Run 38041795993, desktop/mobile 2/2 passed.

- v0.1.0-dev.3: 12 actual HA 2026.10 Core functional tests including menu JSON export/preview/restore, non-admin denial, cross-instance import, conflict rejection and same-title entries. Run https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38043711432.
- Chromium UI test 2/2 passed with simulated HA WebSocket including download + preview + confirmation (same run). Real HA frontend is still outstanding.
- Official HACS structure validation 9/9 passed: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38043711445.

- v0.1.0-dev.4: real upstream 2026.4.13 ConfigEntry layout fixture and HA OptionsFlow migration, cross-host restore of icon/permissions/enabled/order, real HA HTTP retrieval of management JS: 16/16 functional tests passed. https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38050016651.
