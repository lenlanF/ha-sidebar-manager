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

- v0.1.0-dev.5 regression: 19/19 HA Core tests passed, including old unknown options kept on native edit, original title-only entries backed up/restored, and saved `core.config_entries` contents. https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38053139374.
- HACS 9/9: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38053139396. Browser/UI backend is still simulated; live HA process restart and original HACS upgrade remain unchecked.

- v0.1.0-dev.6: `cross-process-config-reload` runs two distinct pytest invocations with a serialized native HA storage envelope in the runner's temporary directory; write/read each pass with the other phase skipped. Source checks run https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38054007697. This is not a full HA Supervisor restart.

- v0.1.0-dev.7: pinned upstream source swap and rollback (`tests/integration/test_upstream_source_swap.py`) in three independent Python processes: original ConfigFlow/save, fork cold load, original-source rollback. All 3 phase tests passed in https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38057571508. Uses genuine upstream commit 90c849d; old options are written via native HA API after old entry unload, not old OptionsFlow UI.

- v0.1.0-dev.8: `tests/live_browser/test_browser_real_ha.py` with HA-native HTTP + authenticated browser WebSocket, 1366px/375px Chromium create/edit/toggle/delete and live ConfigEntry assertions. **2/2 passed** (https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38059902505). Runs in separate GitHub Actions job; not a full HA frontend-shell acceptance test.
- Chromium 153 Local Network Access checks block synthetic Playwright HTML origins. The live test instead has HA HTTP serve `tests/live_browser/host.html`; browser security is not disabled.
