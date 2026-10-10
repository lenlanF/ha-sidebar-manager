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


@pytest.mark.asyncio
async def test_menu_enabled_toggle_controls_native_sidebar_panel(hass):
    """Disable/enable an entry without deleting its config or the manager."""
    from homeassistant.components import frontend

    assert await setup.async_setup_component(hass, "frontend", {})
    menu = MockConfigEntry(
        domain=DOMAIN,
        title="设备入口",
        data={"url": "/config/integrations", "mode": "3"},
        entry_id="toggle-menu-test",
    )
    menu.add_to_hass(hass)
    assert await hass.config_entries.async_setup(menu.entry_id)
    await hass.async_block_till_done()
    assert frontend.async_panel_exists(hass, menu.entry_id)
    assert frontend.async_panel_exists(hass, "ha-sidebar-manager")

    hass.config_entries.async_update_entry(menu, options={"enabled": False})
    await hass.async_block_till_done()
    assert not frontend.async_panel_exists(hass, menu.entry_id)
    assert frontend.async_panel_exists(hass, "ha-sidebar-manager")
    assert menu.options["enabled"] is False

    hass.config_entries.async_update_entry(menu, options={"enabled": True})
    await hass.async_block_till_done()
    assert frontend.async_panel_exists(hass, menu.entry_id)
    assert menu.options["enabled"] is True


@pytest.mark.asyncio
async def test_backup_preflight_and_safe_restore_of_legacy_entries(hass, hass_ws_client):
    """Real WS backup/restore preserves legacy entries, with dry-run and no delete."""
    from homeassistant.components import frontend

    assert await setup.async_setup_component(hass, "frontend", {})
    manager = MockConfigEntry(
        domain=DOMAIN, title="HA Sidebar Manager", data={"manager_only": True},
        entry_id="manager-backup-test",
    )
    legacy = MockConfigEntry(
        domain=DOMAIN, title="旧菜单",
        data={"title": "旧菜单", "legacy_extra": "keep"},
        options={
            "url": "/config/logs", "mode": "3", "icon": "mdi:file",
            "require_admin": True, "legacy_setting": "retain",
        },
        entry_id="legacy-backup-test",
    )
    for entry in (manager, legacy):
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id({"type": "panel_iframe/manager/backup"})
    response = await ws.receive_json()
    assert response["success"], response
    snapshot = response["result"]
    assert snapshot["format"] == "ha-sidebar-manager"
    assert snapshot["version"] == 1
    assert len(snapshot["items"]) == 1
    assert snapshot["items"][0]["entry_id"] == legacy.entry_id
    assert snapshot["items"][0]["url"] == "/config/logs"
    assert "legacy_extra" not in snapshot["items"][0]

    hass.config_entries.async_update_entry(
        legacy, options={**legacy.options, "url": "/config/integrations"}
    )
    await hass.async_block_till_done()
    assert frontend.async_panel_exists(hass, legacy.entry_id)

    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore", "backup": snapshot
    })
    preview = await ws.receive_json()
    assert preview["success"], preview
    assert preview["result"]["counts"] == {"create": 0, "update": 1, "skip": 0}
    assert preview["result"]["applied"] is False
    assert legacy.options["url"] == "/config/integrations"

    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore",
        "backup": snapshot, "apply": True,
    })
    restored = await ws.receive_json()
    assert restored["success"], restored
    assert restored["result"]["applied"] is True
    await hass.async_block_till_done()
    assert legacy.options["url"] == "/config/logs"
    assert legacy.options["legacy_setting"] == "retain"
    assert legacy.data["legacy_extra"] == "keep"
    assert frontend.async_panel_exists(hass, legacy.entry_id)
    assert len(hass.config_entries.async_entries(DOMAIN)) == 2

    # Idempotent re-import does not duplicate a restored menu.
    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore", "backup": snapshot,
    })
    identical = await ws.receive_json()
    assert identical["success"], identical
    assert identical["result"]["counts"] == {"create": 0, "update": 0, "skip": 1}


@pytest.mark.asyncio
async def test_restore_rejects_conflicting_or_malformed_snapshot(hass, hass_ws_client):
    """Do not mutate any entry if preflight detects a title conflict or bad version."""
    assert await setup.async_setup_component(hass, "frontend", {})
    bootstrap = MockConfigEntry(
        domain=DOMAIN, title="HA Sidebar Manager",
        data={"manager_only": True}, entry_id="bootstrap-bad-backup",
    )
    old = MockConfigEntry(
        domain=DOMAIN, title="旧菜单",
        data={"url": "/config/logs", "mode": "3"},
        entry_id="old-bad-backup",
    )
    for entry in (bootstrap, old):
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id({"type": "panel_iframe/manager/backup"})
    valid = (await ws.receive_json())["result"]

    conflicting = {
        **valid,
        "items": [{**valid["items"][0],
                   "entry_id": "other-instance-id",
                   "url": "/config/integrations"}],
    }
    for bad in ({**valid, "version": 999}, conflicting):
        await ws.send_json_auto_id({
            "type": "panel_iframe/manager/restore", "backup": bad,
            "apply": True,
        })
        result = await ws.receive_json()
        assert result["success"] is False, result
        assert len(hass.config_entries.async_entries(DOMAIN)) == 2
        assert old.data["url"] == "/config/logs"


@pytest.mark.asyncio
async def test_non_admin_backup_restore_is_forbidden(hass, hass_ws_client):
    """Read-only HA users are denied for both export and restore."""
    from homeassistant.auth.const import GROUP_ID_READ_ONLY

    assert await setup.async_setup_component(hass, "frontend", {})
    manager = MockConfigEntry(
        domain=DOMAIN, title="HA Sidebar Manager",
        data={"manager_only": True}, entry_id="bootstrap-nonadmin-backup",
    )
    manager.add_to_hass(hass)
    assert await hass.config_entries.async_setup(manager.entry_id)
    await hass.async_block_till_done()
    user = await hass.auth.async_create_user(
        "backup-readonly", group_ids=[GROUP_ID_READ_ONLY]
    )
    refresh = await hass.auth.async_create_refresh_token(
        user, client_id="https://sidebar-manager.test/"
    )
    ws = await hass_ws_client(
        hass, access_token=hass.auth.async_create_access_token(refresh)
    )
    await ws.send_json_auto_id({"type": "panel_iframe/manager/backup"})
    response = await ws.receive_json()
    assert not response["success"], response
    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore",
        "backup": {"format": "ha-sidebar-manager", "version": 1, "items": []},
    })
    response = await ws.receive_json()
    assert not response["success"], response


@pytest.mark.asyncio
async def test_restore_creates_missing_entry_and_reimport_skips_duplicate(hass, hass_ws_client):
    """Cross-instance backup import creates a missing menu without inventing an entry ID."""
    assert await setup.async_setup_component(hass, "frontend", {})
    bootstrap = MockConfigEntry(
        domain=DOMAIN, title="HA Sidebar Manager",
        data={"manager_only": True}, entry_id="bootstrap-cross-import",
    )
    bootstrap.add_to_hass(hass)
    assert await hass.config_entries.async_setup(bootstrap.entry_id)
    await hass.async_block_till_done()

    ws = await hass_ws_client(hass)
    empty = {
        "format": "ha-sidebar-manager", "version": 1,
        "exported_at": "2026-10-10T00:00:00+00:00", "items": [],
    }
    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore", "backup": empty,
    })
    check = await ws.receive_json()
    assert check["success"] and check["result"]["plan"] == [], check

    imported = {
        **empty,
        "items": [{
            "entry_id": "original-instance-only-id",
            "title": "设备与服务", "url": "/config/integrations",
            "icon": "mdi:devices", "mode": "3", "enabled": True,
            "require_admin": True, "menu_order": 0,
        }],
    }
    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore", "backup": imported,
    })
    preview = await ws.receive_json()
    assert preview["success"] and preview["result"]["counts"]["create"] == 1

    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore",
        "backup": imported, "apply": True,
    })
    result = await ws.receive_json()
    assert result["success"] and result["result"]["applied"], result
    await hass.async_block_till_done()
    entries = [
        x for x in hass.config_entries.async_entries(DOMAIN)
        if not x.data.get("manager_only")
    ]
    assert len(entries) == 1
    assert entries[0].title == "设备与服务"
    assert entries[0].entry_id != "original-instance-only-id"

    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore", "backup": imported,
    })
    preview = await ws.receive_json()
    assert preview["success"] and preview["result"]["counts"] == {
        "create": 0, "update": 0, "skip": 1,
    }, preview


@pytest.mark.asyncio
async def test_backup_preserves_distinct_legacy_entries_sharing_same_title(hass, hass_ws_client):
    """A shared display title must not cause legacy entries to be lost."""
    assert await setup.async_setup_component(hass, "frontend", {})
    entries = [
        MockConfigEntry(
            domain=DOMAIN, title="同名菜单", entry_id="duplicate-name-a",
            data={"url": "/config/logs", "mode": "3"},
        ),
        MockConfigEntry(
            domain=DOMAIN, title="同名菜单", entry_id="duplicate-name-b",
            data={"url": "/config/integrations", "mode": "3"},
        ),
    ]
    for entry in entries:
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id({"type": "panel_iframe/manager/backup"})
    snapshot = (await ws.receive_json())["result"]
    assert len(snapshot["items"]) == 2

    hass.config_entries.async_update_entry(
        entries[1], options={"url": "/config/automation/dashboard"}
    )
    await hass.async_block_till_done()

    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore", "backup": snapshot,
    })
    preview = await ws.receive_json()
    assert preview["success"], preview
    assert preview["result"]["counts"] == {"create": 0, "update": 1, "skip": 1}

    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore", "backup": snapshot, "apply": True,
    })
    restored = await ws.receive_json()
    assert restored["success"] and restored["result"]["applied"], restored
    await hass.async_block_till_done()
    assert {x.entry_id: {**x.data, **x.options}["url"] for x in entries} == {
        "duplicate-name-a": "/config/logs",
        "duplicate-name-b": "/config/integrations",
    }
    assert len(hass.config_entries.async_entries(DOMAIN)) == 2


@pytest.mark.asyncio
async def test_real_upstream_entry_layout_survives_plugin_upgrade(hass, hass_ws_client):
    """Load a fixture shaped exactly like upstream 2026.4.13 config-flow records.

    This exercises the NEW code against representative OLD entries without
    claiming a HACS-managed source replacement has occurred.
    """
    import json
    from pathlib import Path
    from homeassistant.components import frontend

    assert await setup.async_setup_component(hass, "frontend", {})
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "upstream_2026_4_13.json"
    records = json.loads(fixture.read_text(encoding="utf-8"))["entries"]
    originals = {}
    for record in records:
        entry = MockConfigEntry(
            domain=DOMAIN, title=record["title"], data=record["data"],
            options=record["options"], entry_id=record["entry_id"],
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        originals[entry.entry_id] = entry
    await hass.async_block_till_done()

    assert frontend.async_panel_exists(hass, "ha-sidebar-manager")
    for record in records:
        assert originals[record["entry_id"]].data == record["data"]
        assert originals[record["entry_id"]].options == record["options"]
        assert frontend.async_panel_exists(
            hass, record["entry_id"]
        ) == bool(record["options"].get("url"))

    ws = await hass_ws_client(hass)
    await ws.send_json_auto_id({"type": "panel_iframe/manager/list"})
    response = await ws.receive_json()
    assert response["success"], response
    items = {x["entry_id"]: x for x in response["result"]}
    assert len(items) == 4
    assert items["old-internal"]["mode"] == "3"
    assert items["old-external"]["url"] == "https://example.org/status"
    assert items["old-external"]["enabled"] is True
    assert items["old-unconfigured"]["configured"] is False
    assert originals["old-external"].options["proxy_access"] is True

    # A new management edit intentionally disables historical unsafe proxying
    # but retains unknown legacy metadata and all other entries.
    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/save", "entry_id": "old-external",
        "title": "旧设备", "url": "https://example.org/status",
        "icon": "mdi:devices", "mode": "0",
        "require_admin": False, "enabled": True,
    })
    saved = await ws.receive_json()
    assert saved["success"], saved
    await hass.async_block_till_done()
    assert originals["old-external"].options["proxy_access"] is False
    assert originals["old-internal"].entry_id == "old-internal"
    assert frontend.async_panel_exists(hass, "old-internal")


@pytest.mark.asyncio
async def test_cross_instance_same_url_restores_different_icon_permissions(hass, hass_ws_client):
    """A title+URL match must update settings instead of silently skipping."""
    assert await setup.async_setup_component(hass, "frontend", {})
    menu = MockConfigEntry(
        domain=DOMAIN, title="状态页",
        data={"title": "状态页"},
        options={
            "url": "/config/logs", "mode": "3", "icon": "mdi:wrong",
            "require_admin": False, "enabled": False, "menu_order": 90,
            "old_extra": "keep",
        },
        entry_id="local-side-id",
    )
    menu.add_to_hass(hass)
    assert await hass.config_entries.async_setup(menu.entry_id)
    ws = await hass_ws_client(hass)
    snapshot = {
        "format": "ha-sidebar-manager", "version": 1,
        "exported_at": "2026-10-10T00:00:00+00:00",
        "items": [{
            "entry_id": "foreign-other-instance-id",
            "title": "状态页", "url": "/config/logs",
            "mode": "3", "icon": "mdi:file-chart",
            "require_admin": True, "enabled": True, "menu_order": 2,
        }],
    }
    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore", "backup": snapshot,
    })
    preview = await ws.receive_json()
    assert preview["success"], preview
    assert preview["result"]["counts"] == {"create": 0, "update": 1, "skip": 0}
    await ws.send_json_auto_id({
        "type": "panel_iframe/manager/restore", "backup": snapshot,
        "apply": True,
    })
    applied = await ws.receive_json()
    assert applied["success"] and applied["result"]["applied"], applied
    await hass.async_block_till_done()
    assert menu.entry_id == "local-side-id"
    assert menu.options["icon"] == "mdi:file-chart"
    assert menu.options["require_admin"] is True
    assert menu.options["enabled"] is True
    assert menu.options["menu_order"] == 2
    assert menu.options["old_extra"] == "keep"


@pytest.mark.asyncio
async def test_upstream_options_flow_can_edit_old_entry(hass):
    """Legacy title-in-data entry remains editable through HA native OptionsFlow."""
    assert await setup.async_setup_component(hass, "frontend", {})
    entry = MockConfigEntry(
        domain=DOMAIN, title="旧服务",
        data={"title": "旧服务", "old_data": "preserved"},
        options={
            "url": "https://example.org", "icon": "mdi:link",
            "mode": "0", "require_admin": False, "proxy_access": True,
            "old_option": "preserved",
        },
        entry_id="upstream-old-options-entry",
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    assert flow["type"] == "form", flow
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {
            "url": "/config/integrations", "icon": "mdi:devices",
            "mode": "3", "require_admin": True, "enabled": True,
        },
    )
    assert result["type"] == "create_entry", result
    await hass.async_block_till_done()
    assert entry.options["url"] == "/config/integrations"
    assert entry.options["proxy_access"] is False
    assert entry.data["old_data"] == "preserved"
