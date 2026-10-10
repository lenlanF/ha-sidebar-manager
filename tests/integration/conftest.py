"""Fixtures for HA Core config-entry functional tests.

Install this checkout as a disposable custom integration in the *test* HA
configuration directory; do not touch any actual Home Assistant installation.
"""

from pathlib import Path
import shutil

import pytest


@pytest.fixture(autouse=True)
def install_plugin_in_disposable_config(hass, enable_custom_integrations):
    """Make the integration discoverable via Home Assistant's normal loader."""
    source = Path(__file__).resolve().parents[2] / "custom_components" / "panel_iframe"
    target = Path(hass.config.path("custom_components", "panel_iframe"))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    yield
