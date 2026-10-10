"""Pin-based upstream source replacement rehearsal using actual HA ConfigEntries.

Two separate pytest/Python processes:
  original: load upstream shaonianzhentan/panel_iframe code pinned at 90c849d,
            create a real ConfigEntry using its ConfigFlow and write native HA store.
  fork:     replace integration files with the fork, then cold-load that store.

No HACS account/site state or production HA files are touched. The original
version may be incompatible with current HA; report that rather than fabricating
a successful original setup.
"""
import json
import os
from pathlib import Path

import pytest
from homeassistant import setup
from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntries, ConfigEntryState, SOURCE_USER


DOMAIN = "panel_iframe"
ENTRY_TITLE = "原始升级菜单"
ENTRY_URL = "/config/automation/dashboard"


def _artifact() -> Path:
    return Path(os.environ["HA_UPGRADE_FILE"])


@pytest.mark.asyncio
async def test_upstream_2026_4_13_creates_and_saves_real_entry(
    hass, hass_storage, freezer,
):
    if os.environ.get("HA_UPGRADE_PHASE") != "original":
        pytest.skip("upstream source creation phase only")
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    source = Path(os.environ["HA_TEST_PLUGIN_SOURCE"])
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == DOMAIN
    assert manifest["version"] == "2026.4.13"

    assert await setup.async_setup_component(hass, "frontend", {})
    flow = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert flow["type"] == "form", flow
    finished = await hass.config_entries.flow.async_configure(
        flow["flow_id"], {"title": ENTRY_TITLE}
    )
    assert finished["type"] == "create_entry", finished
    await hass.async_block_till_done()

    records = hass.config_entries.async_entries(DOMAIN)
    assert len(records) == 1
    entry = records[0]
    assert entry.title == ENTRY_TITLE
    assert entry.data == {"title": ENTRY_TITLE}

    # Preserve the actual upstream ConfigEntry layout: options are the user's
    # settings from the upstream OptionsFlow.
    hass.config_entries.async_update_entry(
        entry,
        options={
            "icon": "mdi:robot",
            "url": ENTRY_URL,
            "mode": "3",
            "require_admin": True,
            "proxy_access": False,
        },
    )
    await hass.async_block_till_done()
    freezer.tick(4)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    envelope = hass_storage["core.config_entries"]
    saved = next(
        x for x in envelope["data"]["entries"] if x["entry_id"] == entry.entry_id
    )
    assert saved["data"] == {"title": ENTRY_TITLE}
    assert saved["options"]["url"] == ENTRY_URL
    assert saved["options"]["icon"] == "mdi:robot"
    _artifact().parent.mkdir(parents=True, exist_ok=True)
    _artifact().write_text(
        json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # Strict boundary: this is source + flow + HA store, not HACS metadata.


@pytest.mark.asyncio
async def test_fork_replaces_upstream_and_loads_native_entry(hass, hass_storage):
    if os.environ.get("HA_UPGRADE_PHASE") != "fork":
        pytest.skip("fork source cold-load phase only")
    from custom_components.panel_iframe import VERSION

    assert VERSION.startswith("0.1.0-dev."), VERSION
    original = json.loads(_artifact().read_text(encoding="utf-8"))
    stored = original["data"]["entries"]
    old = next(x for x in stored if x["domain"] == DOMAIN)
    old_entry_id = old["entry_id"]
    hass_storage["core.config_entries"] = original
    entries = ConfigEntries(hass, {})
    await entries.async_initialize()
    hass.config_entries = entries

    found = entries.async_get_entry(old_entry_id)
    assert found is not None
    assert found.domain == DOMAIN
    assert found.title == ENTRY_TITLE
    assert found.data == {"title": ENTRY_TITLE}
    assert found.options["url"] == ENTRY_URL
    assert found.options["icon"] == "mdi:robot"
    assert found.options["require_admin"] is True
    assert found.options["proxy_access"] is False

    assert await setup.async_setup_component(hass, "frontend", {})
    await hass.async_block_till_done()
    if found.state is ConfigEntryState.NOT_LOADED:
        assert await entries.async_setup(found.entry_id)
    await hass.async_block_till_done()
    assert found.state is ConfigEntryState.LOADED
    assert frontend.async_panel_exists(hass, old_entry_id)
    assert frontend.async_panel_exists(hass, "ha-sidebar-manager")
    # The upstream ID, UI title and options survive the fork source switch.
    assert len(entries.async_entries(DOMAIN)) == 1
    assert found.entry_id == old_entry_id
