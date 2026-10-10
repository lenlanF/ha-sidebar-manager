"""Fixtures for Home Assistant integration tests (real HA Core API)."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load custom_components from this repository."""
    yield
