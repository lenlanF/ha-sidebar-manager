"""Administrator-only WebSocket management for panel_iframe entries.

Every sidebar item remains a native Home Assistant ConfigEntry, including
entries installed with the upstream panel_iframe integration. No parallel
database is introduced and no Home Assistant core files are modified.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant, callback

from .backup import BackupValidationError, make_backup, prepare_restore
from .config_flow import DOMAIN, _validate

WS_PREFIX = "panel_iframe/manager/"


def _entries(hass: HomeAssistant):
    return [entry for entry in hass.config_entries.async_entries(DOMAIN)
            if not entry.data.get("manager_only")]


def _item(entry) -> dict[str, Any]:
    values = {**entry.data, **entry.options}
    return {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "url": values.get("url", ""),
        "icon": values.get("icon", "mdi:link-box-outline"),
        "mode": str(values.get("mode", "0")),
        "require_admin": bool(values.get("require_admin", False)),
        "menu_order": values.get("menu_order", 100000),
        "configured": bool(values.get("url")),
        "enabled": bool(values.get("enabled", True)),
    }


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register once per HA process, even with multiple config entries."""
    for handler in (ws_list, ws_save, ws_delete, ws_reorder, ws_backup, ws_restore):
        websocket_api.async_register_command(hass, handler)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_PREFIX + "list"})
@callback
def ws_list(hass, connection, msg) -> None:
    """List legacy and new menu entries in one management screen."""
    items = [_item(entry) for entry in _entries(hass)]
    items.sort(key=lambda x: (x["menu_order"], x["title"].casefold(), x["entry_id"]))
    connection.send_result(msg["id"], items)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_PREFIX + "save",
        vol.Optional("entry_id"): str,
        vol.Required("title"): str,
        vol.Required("url"): str,
        vol.Required("icon"): str,
        vol.Required("mode"): vol.In(("0", "1", "2", "3")),
        vol.Required("require_admin"): bool,
        vol.Optional("enabled"): bool,
    }
)
@websocket_api.async_response
async def ws_save(hass, connection, msg) -> None:
    """Create via the native config flow or update an existing config entry."""
    entry_id = msg.get("entry_id")
    entry = None
    if entry_id:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN or entry.data.get("manager_only"):
            connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND,
                                  "Sidebar entry not found")
            return

    payload = {key: msg[key] for key in
               ("title", "url", "icon", "mode", "require_admin")}
    if "enabled" in msg:
        payload["enabled"] = msg["enabled"]
    # Original panel_iframe can have title-only entries. Permit keeping a
    # missing URL while editing THAT entry, but never allow newly created
    # entries or already configured menus to have their URLs cleared.
    current = {**entry.data, **entry.options} if entry else {}
    values, errors = _validate(
        payload, allow_unconfigured=bool(entry and not current.get("url"))
    )
    if errors:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT,
                              ", ".join(f"{key}: {error}" for key, error in errors.items()))
        return

    try:
        if entry is not None:
            title = values.pop("title")
            updated_options = {**entry.options, **values}
            old_title = entry.title
            old_options = entry.options
            hass.config_entries.async_update_entry(
                entry, title=title, options=updated_options
            )
            # Changes in options trigger the entry's update listener. Only a
            # title-only change needs an explicit reload to refresh the panel.
            if updated_options == old_options and title != old_title:
                await hass.config_entries.async_reload(entry.entry_id)
            connection.send_result(msg["id"], {"entry_id": entry_id})
            return

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=values
        )
        if result["type"] != "create_entry":
            connection.send_error(msg["id"], "flow_incomplete",
                                  "Home Assistant did not create the new entry")
            return
        connection.send_result(msg["id"], {"created": True})
    except Exception as err:
        connection.send_error(msg["id"], "save_failed", str(err))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): WS_PREFIX + "delete", vol.Required("entry_id"): str}
)
@websocket_api.async_response
async def ws_delete(hass, connection, msg) -> None:
    """Remove only this integration's config entries."""
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN or entry.data.get('manager_only'):
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND,
                              "Sidebar entry not found")
        return
    try:
        await hass.config_entries.async_remove(entry.entry_id)
    except Exception as err:
        connection.send_error(msg["id"], "delete_failed", str(err))
        return
    connection.send_result(msg["id"], {"deleted": True})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): WS_PREFIX + "reorder",
     vol.Required("entry_ids"): [str]}
)
@websocket_api.async_response
async def ws_reorder(hass, connection, msg) -> None:
    """Persist manager list order. Native HA sidebar ordering is user-managed."""
    ids = msg["entry_ids"]
    entries = _entries(hass)
    if len(ids) != len(entries) or len(set(ids)) != len(ids) or (
        set(ids) != {entry.entry_id for entry in entries}
    ):
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT,
                              "Reorder must contain each sidebar entry exactly once")
        return
    indexed = {entry.entry_id: entry for entry in entries}
    for index, entry_id in enumerate(ids):
        entry = indexed[entry_id]
        if entry.options.get("menu_order") == index:
            continue
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, "menu_order": index}
        )
    connection.send_result(msg["id"], {"saved": True})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_PREFIX + "backup"})
@callback
def ws_backup(hass, connection, msg) -> None:
    """Read-only JSON snapshot; browser downloads this locally."""
    try:
        rows = [_item(entry) for entry in _entries(hass)]
        backup = make_backup(rows, datetime.now(timezone.utc).isoformat())
    except BackupValidationError as err:
        connection.send_error(msg["id"], "backup_failed", str(err))
        return
    connection.send_result(msg["id"], backup)


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): WS_PREFIX + "restore",
    vol.Required("backup"): dict,
    vol.Optional("apply", default=False): bool,
})
@websocket_api.async_response
async def ws_restore(hass, connection, msg) -> None:
    """Dry-run preflight by default; explicit apply never deletes a menu.

    Apply can partially succeed if HA fails during a create/update.
    Report each completed operation rather than claiming atomic rollback.
    """
    lock = hass.data.setdefault(f"{DOMAIN}_restore_lock", asyncio.Lock())
    async with lock:
        try:
            existing = [_item(entry) for entry in _entries(hass)]
            normalized, plan = prepare_restore(msg["backup"], existing, _validate)
        except BackupValidationError as err:
            connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, str(err))
            return

        counts = {
            action: sum(item["action"] == action for item in plan)
            for action in ("create", "update", "skip")
        }
        if not msg.get("apply", False):
            connection.send_result(msg["id"], {"plan": plan, "counts": counts, "applied": False})
            return

        completed = []
        for item in plan:
            index = item["index"]
            action = item["action"]
            if action == "skip":
                continue
            values = dict(normalized[index])
            try:
                if action == "update":
                    entry = hass.config_entries.async_get_entry(item["entry_id"])
                    if entry is None or entry.domain != DOMAIN or entry.data.get("manager_only"):
                        raise ValueError("Entry no longer exists")
                    title = values.pop("title")
                    options = {**entry.options, **values}
                    old_title, old_options = entry.title, entry.options
                    hass.config_entries.async_update_entry(entry, title=title, options=options)
                    if old_options == options and old_title != title:
                        await hass.config_entries.async_reload(entry.entry_id)
                    completed.append({"action": action, "entry_id": entry.entry_id})
                else:
                    if not values.get("url"):
                        # Preserve an old config entry that never had a URL.
                        # Normal UI creation still requires a valid URL.
                        values["restore_unconfigured"] = True
                    result = await hass.config_entries.flow.async_init(
                        DOMAIN, context={"source": SOURCE_USER}, data=values
                    )
                    if result.get("type") != "create_entry":
                        raise RuntimeError("Home Assistant did not create the menu")
                    new_entry = result.get("result")
                    completed.append({
                        "action": action,
                        "entry_id": new_entry.entry_id if new_entry else None,
                    })
            except Exception as err:
                connection.send_result(msg["id"], {
                    "applied": False,
                    "partial": bool(completed),
                    "completed": completed,
                    "failed_index": index,
                    "error": str(err),
                    "counts": counts,
                })
                return
        connection.send_result(msg["id"], {
            "applied": True, "partial": False, "completed": completed,
            "counts": counts,
        })
