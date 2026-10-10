"""Functional HA Core integration tests; not isolated mock tests."""

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant import setup
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "panel_iframe"


@pytest.mark.asyncio
async def test_manager_install_via_config_flow(hass):
    """A real HA config flow creates and sets up a manager-only entry."""
    await setup.async_setup_component(hass, "frontend", {})
    first = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert first["type"] == "form", first
    result = await hass.config_entries.flow.async_configure(
        first["flow_id"], {"setup_type": "manager"}
    )
    assert result["type"] == "create_entry", result
    assert result["data"]["manager_only"] is True
    await hass.async_block_till_done()
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert hass.data.get("panel_iframe_manager_registered") is True

    again = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER},
        data={"setup_type": "manager"},
    )
    assert again["type"] == "abort"
    assert again["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_legacy_entries_and_native_reload(hass):
    """Multiple old-format entries do not duplicate shared paths/panels."""
    await setup.async_setup_component(hass, "frontend", {})
    manager = MockConfigEntry(
        domain=DOMAIN,
        title="HA Sidebar Manager",
        data={"manager_only": True},
        entry_id="mgr-test",
    )
    old = MockConfigEntry(
        domain=DOMAIN,
        title="自动化",
        data={"title": "自动化"},
        options={"url": "/config/automation/dashboard", "mode": "3"},
        entry_id="old-test",
    )
    second = MockConfigEntry(
        domain=DOMAIN,
        title="集成",
        data={"url": "/config/integrations", "mode": "3"},
        entry_id="second-test",
    )
    for entry in (manager, old, second):
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.data["panel_iframe_static_registered"]
    assert hass.data["panel_iframe_manager_registered"]
    assert len(hass.config_entries.async_entries(DOMAIN)) == 3

    hass.config_entries.async_update_entry(
        old, options={"url": "/config/logs", "mode": "3"}
    )
    await hass.async_block_till_done()
    assert {**old.data, **old.options}["url"] == "/config/logs"

    assert await hass.config_entries.async_reload(second.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(old.entry_id)
    await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_create_sidebar_entry_from_native_flow(hass):
    """New entries accept complete config without a second options step."""
    await setup.async_setup_component(hass, "frontend", {})
    first = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert first["type"] == "form"
    step = await hass.config_entries.flow.async_configure(
        first["flow_id"], {"setup_type": "item"}
    )
    assert step["type"] == "form", step
    result = await hass.config_entries.flow.async_configure(
        step["flow_id"],
        {"title": "设备管理", "url": "/config/integrations",
         "icon": "mdi:devices", "mode": "3", "require_admin": True},
    )
    assert result["type"] == "create_entry", result
    await hass.async_block_till_done()
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].title == "设备管理"
    assert entries[0].data["url"] == "/config/integrations"
