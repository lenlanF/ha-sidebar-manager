# Testing tiers

**Executed in GitHub Actions (see DEVELOPMENT_LOG.md for exact run IDs):**
- Python syntax compilation, JSON parsing, JavaScript syntax.
- Isolated `tests/test_validation_isolated.py` and `tests/test_manager_isolated.py` with fake Home Assistant objects.
- Core import smoke on a Home Assistant-compatible Python interpreter.

**Not yet executed:**
- Running HA instance with integration installation, multiple ConfigEntry reloads, real WebSocket CRUD and removal.
- Browser/mobile UI tests, Ingress routing, permissions and CSP/iframe behavior.
- Upgrade-over-legacy and rollback testing.

Isolated tests are deliberately not labeled as full integration tests.
