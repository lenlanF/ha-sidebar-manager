# Test notes

These tests are regression specifications, not evidence of successful HA integration tests.

- Unit checks: `python -m pytest tests/test_config_validation.py`
- Real HA environment: config flow create/options/delete, multiple entries, update reload, old-entry migration and sidebar navigation.
- Browser tests: desktop/mobile, 2025.12+ and a supported recent 2026 HA release.
- Security checks: no unauthenticated proxy route; iframe restrictions and internal-route allowlist design.

No test command has yet been executed by CI or a connected HA instance in this repository.
