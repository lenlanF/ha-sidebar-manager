"""Config and options flows for HA Sidebar Manager (legacy domain preserved)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback

DOMAIN = "panel_iframe"
MODES = {"0": "嵌入", "1": "全屏", "2": "新窗口", "3": "HA 内部路径"}


def _fields(defaults: dict[str, Any], *, include_title: bool) -> vol.Schema:
    fields = {}
    if include_title:
        fields[vol.Required("title", default=defaults.get("title", ""))] = str
    fields[vol.Required("url", default=defaults.get("url", ""))] = str
    fields[vol.Required("icon", default=defaults.get("icon", "mdi:link-box-outline"))] = str
    fields[vol.Required("mode", default=str(defaults.get("mode", "0")))] = vol.In(MODES)
    fields[vol.Required("require_admin", default=defaults.get("require_admin", False))] = bool
    return vol.Schema(fields)


def _validate(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    values = dict(data)
    errors: dict[str, str] = {}
    if "title" in values:
        values["title"] = values["title"].strip()
        if not values["title"]:
            errors["title"] = "required"
    values["url"] = values["url"].strip()
    if not values["url"]:
        errors["url"] = "required"
    values["icon"] = values["icon"].strip().replace("mdi-", "mdi:", 1)
    if not values["icon"]:
        errors["icon"] = "required"
    if values["mode"] == "3" and (
        not values["url"].startswith("/")
        or values["url"].startswith("//")
        or "\\" in values["url"]
    ):
        errors["url"] = "invalid_internal_path"
    if values["mode"] != "3" and not (
        values["url"].startswith(("http://", "https://", "/"))
        or values["url"].isdigit()
        or values["url"].startswith(":")
    ):
        errors["url"] = "invalid_url"
    values["proxy_access"] = False
    return values, errors


class SidebarConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Install the manager, or create a sidebar item with the native flow."""
        if user_input is not None:
            # WebSocket-created entries pass fields directly to the user step.
            if "url" in user_input:
                return await self.async_step_item(user_input)
            if user_input.get("setup_type") == "item":
                return await self.async_step_item()
            if user_input.get("setup_type") == "manager":
                if any(e.data.get("manager_only") for e in self._async_current_entries()):
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(
                    title="HA Sidebar Manager", data={"manager_only": True}
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("setup_type", default="manager"): vol.In({
                    "manager": "安装侧边栏管理器",
                    "item": "创建单个侧边栏入口",
                })
            }),
        )

    async def async_step_item(self, user_input: dict[str, Any] | None = None):
        """Preserve the legacy one-entry-per-menu format."""
        if user_input is not None:
            values, errors = _validate(user_input)
            if not errors:
                title = values.pop("title")
                return self.async_create_entry(title=title, data=values)
        else:
            errors = {}
        return self.async_show_form(
            step_id="item",
            data_schema=_fields(user_input or {}, include_title=True),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        return SidebarOptionsFlow()


class SidebarOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            values, errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title="", data=values)
        else:
            errors = {}
        defaults = dict(self.config_entry.data)
        defaults.update(self.config_entry.options)
        return self.async_show_form(
            step_id="init",
            data_schema=_fields(user_input or defaults, include_title=False),
            errors=errors,
        )
