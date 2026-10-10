"""Fixtures for HA Core tests in disposable Home Assistant config directories.

HA_TEST_PLUGIN_SOURCE optionally points to an independently checked out
original panel_iframe source tree. Never touch an actual HA installation.
"""
import os
from pathlib import Path
import shutil

import pytest


@pytest.fixture(autouse=True)
def install_plugin_in_disposable_config(hass, enable_custom_integrations):
    """Install the selected source under the legacy HA integration domain."""
    default = Path(__file__).resolve().parents[2] / "custom_components" / "panel_iframe"
    source = Path(os.environ.get("HA_TEST_PLUGIN_SOURCE", str(default))).resolve()
    assert (source / "manifest.json").is_file(), source
    assert source.name == "panel_iframe", source
    target = Path(hass.config.path("custom_components", "panel_iframe"))
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
    yield
