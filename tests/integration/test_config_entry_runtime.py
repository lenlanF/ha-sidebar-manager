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


@pytest.mark.asyncio
async def test_real_websocket_crud(hass, hass_ws_client):
    """Manage real config entries through HA's authenticated WebSocket."""
    await setup.async_setup_component(hass, "frontend", {})
    manager = MockConfigEntry(
        domain=DOMAIN,
        title="HA Sidebar Manager",
        data={"manager_only": True},
        entry_id="mgr-websocket-test",
    )
    manager.add_to_hass(hass)
    assert await hass.config_entries.async_setup(manager.entry_id)
    await hass.async_block_till_done()

    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id({"type": "panel_iframe/manager/list"})
    listed = await ws.receive_json()
    assert listed["success"], listed
    assert listed["result"] == [], listed

    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/save",
        "title": "HA 集成",
        "url": "/config/integrations",
        "icon": "mdi:devices",
        "mode": "3",
        "require_admin": True,
    })
    created = await ws.receive_json()
    assert created["success"], created
    await hass.async_block_till_done()

    await ws.send_json_auto_id({"type": "panel_iframe/manager/list"})
    listed = await ws.receive_json()
    assert listed["success"], listed
    assert len(listed["result"]) == 1, listed
    item = listed["result"][0]
    assert item["title"] == "HA 集成"
    assert item["url"] == "/config/integrations"
    item_id = item["entry_id"]

    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/save",
        "entry_id": item_id,
        "title": "自动化管理",
        "url": "/config/automation/dashboard",
        "icon": "mdi:robot",
        "mode": "3",
        "require_admin": True,
    })
    updated = await ws.receive_json()
    assert updated["success"], updated
    await hass.async_block_till_done()

    await ws.send_json_auto_id({"type": "panel_iframe/manager/list"})
    listed = await ws.receive_json()
    assert listed["result"][0]["title"] == "自动化管理"
    assert listed["result"][0]["url"] == "/config/automation/dashboard"

    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/delete", "entry_id": item_id
    })
    deleted = await ws.receive_json()
    assert deleted["success"], deleted
    await hass.async_block_till_done()
    assert hass.config_entries.async_get_entry(item_id) is None

    # The setup manager cannot be removed via the menu deletion endpoint.
    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/delete", "entry_id": manager.entry_id
    })
    denied = await ws.receive_json()
    assert denied["success"] is False, denied


@pytest.mark.asyncio
async def test_websocket_non_admin_cannot_manage_menus(hass, hass_ws_client):
    """Read-only users must be denied by backend, not just the manager UI."""
    from homeassistant.auth.const import GROUP_ID_READ_ONLY

    await setup.async_setup_component(hass, "frontend", {})
    manager = MockConfigEntry(
        domain=DOMAIN,
        title="HA Sidebar Manager",
        data={"manager_only": True},
        entry_id="mgr-nonadmin-test",
    )
    manager.add_to_hass(hass)
    assert await hass.config_entries.async_setup(manager.entry_id)
    await hass.async_block_till_done()

    user = await hass.auth.async_create_user(
        "sidebar-readonly", group_ids=[GROUP_ID_READ_ONLY]
    )
    token = await hass.auth.async_create_refresh_token(user, client_id="https://sidebar-manager.test/")
    access_token = hass.auth.async_create_access_token(token)
    ws = await hass_ws_client(hass, access_token=access_token)

    await ws.send_json_auto_id({"type": "panel_iframe/manager/list"})
    response = await ws.receive_json()
    assert response["success"] is False, response

    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/save",
        "title": "Forbidden",
        "url": "/config/integrations",
        "icon": "mdi:devices",
        "mode": "3",
        "require_admin": False,
    })
    response = await ws.receive_json()
    assert response["success"] is False, response
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


@pytest.mark.asyncio
async def test_shared_manager_lifecycle_and_return_after_reload(hass):
    """Keep the manager while any entry is active; remove it after the last unload."""
    from homeassistant.components import frontend

    assert await setup.async_setup_component(hass, "frontend", {})
    bootstrap = MockConfigEntry(
        domain=DOMAIN,
        title="HA Sidebar Manager",
        data={"manager_only": True},
        entry_id="manager-lifecycle-test",
    )
    menu = MockConfigEntry(
        domain=DOMAIN,
        title="集成入口",
        data={"url": "/config/integrations", "mode": "3"},
        entry_id="menu-lifecycle-test",
    )
    for entry in (bootstrap, menu):
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert frontend.async_panel_exists(hass, "ha-sidebar-manager")
    assert frontend.async_panel_exists(hass, menu.entry_id)

    assert await hass.config_entries.async_unload(bootstrap.entry_id)
    await hass.async_block_till_done()
    assert frontend.async_panel_exists(hass, "ha-sidebar-manager")
    assert frontend.async_panel_exists(hass, menu.entry_id)

    assert await hass.config_entries.async_unload(menu.entry_id)
    await hass.async_block_till_done()
    assert not frontend.async_panel_exists(hass, "ha-sidebar-manager")
    assert not frontend.async_panel_exists(hass, menu.entry_id)
    assert not hass.data["panel_iframe_manager_registered"]
    assert hass.data["panel_iframe_manager_commands_registered"]
    assert hass.data["panel_iframe_active_entry_ids"] == set()

    # A later re-setup must restore the panel without re-registering WS commands.
    assert await hass.config_entries.async_setup(bootstrap.entry_id)
    await hass.async_block_till_done()
    assert frontend.async_panel_exists(hass, "ha-sidebar-manager")
    assert hass.data["panel_iframe_manager_commands_registered"]
    assert hass.data["panel_iframe_active_entry_ids"] == {bootstrap.entry_id}
