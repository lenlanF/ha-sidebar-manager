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
