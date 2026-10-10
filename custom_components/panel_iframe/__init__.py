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


async def _register_static_once(hass: HomeAssistant) -> None:
    """Register shared web resources once even with concurrent config entries."""
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
    lock = hass.data.get(MANAGER_LOCK)
    if lock is None:
        lock = hass.data[MANAGER_LOCK] = asyncio.Lock()
    async with lock:
        if hass.data.get(MANAGER_FLAG):
            return
        await async_register_panel(
            hass,
            frontend_url_path="ha-sidebar-manager",
            webcomponent_name="ha-sidebar-manager-panel",
            sidebar_title="侧边栏管理",
            sidebar_icon="mdi:view-dashboard-edit",
            module_url=f"/panel_iframe_www/manager.js?v={VERSION}",
            config={},
            require_admin=True,
        )
        async_register_commands(hass)
        hass.data[MANAGER_FLAG] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await _register_static_once(hass)
    await _register_manager_once(hass)
    config = {**entry.data, **entry.options}
    url = config.get("url")
    if url:
        # Historical proxy_access option is preserved but deliberately not used.
        # The upstream wildcard HTTP proxy has no authorization guard.
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
    entry.async_on_unload(entry.add_update_listener(_update_listener))
    return True


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if {**entry.data, **entry.options}.get('url'):
        frontend.async_remove_panel(hass, entry.entry_id)
    entry.async_unload_callbacks()
    return True
