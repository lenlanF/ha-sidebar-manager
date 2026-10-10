"""Compatibility layer for upstream panel_iframe config entries."""

import asyncio

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.panel_custom import async_register_panel
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .manifest import manifest
from .manager_api import async_register_commands

DOMAIN = manifest.domain
VERSION = manifest.version
STATIC_FLAG = f"{DOMAIN}_static_registered"
STATIC_LOCK = f"{DOMAIN}_static_lock"
MANAGER_FLAG = f"{DOMAIN}_manager_registered"
MANAGER_LOCK = f"{DOMAIN}_manager_lock"
MANAGER_COMMANDS_FLAG = f"{DOMAIN}_manager_commands_registered"
ACTIVE_ENTRIES = f"{DOMAIN}_active_entry_ids"
MANAGER_PATH = "ha-sidebar-manager"


async def _register_static_once(hass: HomeAssistant) -> None:
    """Register shared web resources only once per HA instance."""
    lock = hass.data.get(STATIC_LOCK)
    if lock is None:
        lock = hass.data[STATIC_LOCK] = asyncio.Lock()
    async with lock:
        if hass.data.get(STATIC_FLAG):
            return
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    "/panel_iframe_www",
                    hass.config.path("custom_components", DOMAIN, "www"),
                    False,
                )
            ]
        )
        hass.data[STATIC_FLAG] = True


async def _register_manager_once(hass: HomeAssistant) -> None:
    """Register one shared manager panel and one set of WebSocket commands."""
    lock = hass.data.get(MANAGER_LOCK)
    if lock is None:
        lock = hass.data[MANAGER_LOCK] = asyncio.Lock()
    async with lock:
        if not hass.data.get(MANAGER_FLAG):
            await async_register_panel(
                hass,
                frontend_url_path=MANAGER_PATH,
                webcomponent_name="ha-sidebar-manager-panel",
                sidebar_title="侧边栏管理",
                sidebar_icon="mdi:view-dashboard-edit",
                module_url=f"/panel_iframe_www/manager.js?v={VERSION}",
                config={},
                require_admin=True,
            )
            hass.data[MANAGER_FLAG] = True
        if not hass.data.get(MANAGER_COMMANDS_FLAG):
            async_register_commands(hass)
            hass.data[MANAGER_COMMANDS_FLAG] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an individual menu or manager bootstrap config entry."""
    await _register_static_once(hass)
    await _register_manager_once(hass)
    config = {**entry.data, **entry.options}
    url = config.get("url")
    if url and not config.get("manager_only") and config.get("enabled", True):
        # Historical proxy_access settings are retained but never executed.
        await async_register_panel(
            hass,
            frontend_url_path=entry.entry_id,
            webcomponent_name="ha-panel_iframe",
            sidebar_title=entry.title,
            sidebar_icon=config.get("icon") or "mdi:link-box-outline",
            module_url=f"/panel_iframe_www/panel_iframe.js?v={VERSION}",
            config={"mode": config.get("mode", "0"), "url": url},
            require_admin=config.get("require_admin", False),
        )
    hass.data.setdefault(ACTIVE_ENTRIES, set()).add(entry.entry_id)
    entry.async_on_unload(entry.add_update_listener(_update_listener))
    return True


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a menu, and remove the shared manager after the last entry."""
    frontend.async_remove_panel(hass, entry.entry_id, warn_if_unknown=False)
    lock = hass.data.get(MANAGER_LOCK)
    if lock is None:
        # Setup was never completed; nothing shared can remain registered.
        return True
    async with lock:
        active = hass.data.setdefault(ACTIVE_ENTRIES, set())
        active.discard(entry.entry_id)
        if not active and hass.data.get(MANAGER_FLAG):
            frontend.async_remove_panel(hass, MANAGER_PATH, warn_if_unknown=False)
            hass.data[MANAGER_FLAG] = False
    # HA executes and clears entry.async_on_unload callbacks automatically.
    # Keep the WebSocket handlers registered: HA does not support unregistering
    # these at runtime, and subsequent entry setups must not register duplicates.
    return True
