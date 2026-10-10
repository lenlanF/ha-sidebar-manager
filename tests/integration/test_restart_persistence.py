"""Two independent pytest processes verifying HA ConfigEntry persistence.

Run first with HA_RESTART_PHASE=write, then read. CI uses two distinct
Python processes and an on-disk JSON artifact in a disposable directory.
The fixture constructs a fresh HA Core ConfigEntries manager for read phase.
This is a real persistence cold-load test, NOT a full supervisor/HA OS restart
and not an upstream HACS repository swap.
"""

import json
import os
from pathlib import Path

import pytest
from homeassistant import setup
from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntries, ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry


def _path() -> Path:
    return Path(os.environ["HA_RESTART_FILE"])


@pytest.mark.asyncio
async def test_write_legacy_entries_to_native_ha_storage(hass, hass_storage, freezer):
    if os.getenv("HA_RESTART_PHASE") != "write":
        pytest.skip("write phase only")

    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    assert await setup.async_setup_component(hass, "frontend", {})
    fixtures = [
        MockConfigEntry(
            domain="panel_iframe",
            title="原版自动化",
            data={"title": "原版自动化", "legacy_marker": "persist-unchanged"},
            options={
                "url": "/config/logs",
                "icon": "mdi:robot",
                "mode": "3",
                "require_admin": True,
                "proxy_access": True,
                "legacy_option": "persist-unchanged",
            },
            entry_id="upgrade-persist-legacy",
        ),
        MockConfigEntry(
            domain="panel_iframe",
            title="未设置地址",
            data={"title": "未设置地址"},
            options={},
            entry_id="upgrade-persist-empty",
        ),
        MockConfigEntry(
            domain="panel_iframe",
            title="HA Sidebar Manager",
            data={"manager_only": True},
            options={},
            entry_id="upgrade-persist-manager",
        ),
    ]
    for entry in fixtures:
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)

    old = fixtures[0]
    hass.config_entries.async_update_entry(
        old,
        options={
            **old.options,
            "url": "/config/integrations",
            "enabled": False,
        },
    )
    await hass.async_block_till_done()
    freezer.tick(2)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    saved = hass_storage["core.config_entries"]
    ids = [row["entry_id"] for row in saved["data"]["entries"]]
    assert set(ids) >= {
        "upgrade-persist-legacy",
        "upgrade-persist-empty",
        "upgrade-persist-manager",
    }
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.mark.asyncio
async def test_new_python_process_loads_original_ids_and_settings(hass, hass_storage):
    if os.getenv("HA_RESTART_PHASE") != "read":
        pytest.skip("read phase only")

    # Read the on-disk HA native storage envelope created in the first process.
    saved = json.loads(_path().read_text(encoding="utf-8"))
    hass_storage["core.config_entries"] = saved
    # Fresh native ConfigEntries object exercises async_initialize from Store.
    entries = ConfigEntries(hass, {})
    await entries.async_initialize()
    hass.config_entries = entries

    actual = {entry.entry_id: entry for entry in entries.async_entries("panel_iframe")}
    assert len(actual) == 3
    legacy = actual["upgrade-persist-legacy"]
    assert legacy.title == "原版自动化"
    assert legacy.data["legacy_marker"] == "persist-unchanged"
    assert legacy.data["title"] == "原版自动化"
    assert legacy.options["url"] == "/config/integrations"
    assert legacy.options["enabled"] is False
    assert legacy.options["proxy_access"] is True
    assert legacy.options["legacy_option"] == "persist-unchanged"
    assert actual["upgrade-persist-empty"].data["title"] == "未设置地址"
    assert actual["upgrade-persist-empty"].options == {}
    assert actual["upgrade-persist-manager"].data["manager_only"] is True

    # Setting up frontend can trigger HA to load every waiting entry; do
    # not call async_setup twice on an entry that is already LOADED.
    assert await setup.async_setup_component(hass, "frontend", {})
    await hass.async_block_till_done()
    for entry in actual.values():
        if entry.state is ConfigEntryState.NOT_LOADED:
            assert await entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert all(e.state is ConfigEntryState.LOADED for e in actual.values())
    assert frontend.async_panel_exists(hass, "ha-sidebar-manager")
    assert not frontend.async_panel_exists(hass, legacy.entry_id)
    assert not frontend.async_panel_exists(hass, "upgrade-persist-empty")
    assert hass.data["panel_iframe_manager_registered"]
