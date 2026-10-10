"""Chromium front end connected to *real* Home Assistant HTTP + WebSocket.

Only the frontend host HTML and hass connection adapter are minimal. The JS
bundle is fetched from HA's registered HTTP static path; every WebSocket
operation is sent to HA Core's actual authenticated /api/websocket server.
This is not a full Home Assistant frontend shell, HACS install, or HAOS boot.
"""

from pathlib import Path

import pytest
from homeassistant import setup
from homeassistant.components.http import StaticPathConfig
from playwright.async_api import async_playwright, expect
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "panel_iframe"

# A tiny real-browser HA connection adapter. There is intentionally no fake
# server, WebSocket response, or menu state here.
CONNECT = r"""
async ({token}) => {
  const scheme = location.protocol === "https:" ? "wss:" : "ws:";
  const socket = new WebSocket(scheme + "//" + location.host + "/api/websocket");
  const waiting = new Map();
  let nextId = 1;
  let accept, rejectReady;
  const ready = new Promise((resolve, reject) => {
    accept = resolve;
    rejectReady = reject;
  });
  socket.addEventListener("error", () => rejectReady(
    new Error("HA WebSocket failed on "+ socket.url + ", readyState=" + socket.readyState)
  ));
  socket.addEventListener("close", (event) => {
    rejectReady(new Error("HA WebSocket closed, code=" + event.code));
  });
  socket.addEventListener("message", (event) => {
    const response = JSON.parse(event.data);
    if (response.type === "auth_required") {
      socket.send(JSON.stringify({type:"auth", access_token:token}));
      return;
    }
    if (response.type === "auth_ok") { accept(); return; }
    if (response.type === "auth_invalid") {
      rejectReady(new Error("HA rejected browser auth token")); return;
    }
    if (response.type !== "result" || !waiting.has(response.id)) return;
    const callbacks = waiting.get(response.id);
    waiting.delete(response.id);
    response.success
      ? callbacks.resolve(response.result)
      : callbacks.reject(new Error(response.error?.message || "WebSocket rejected command"));
  });
  await ready;
  const panel = document.createElement("ha-sidebar-manager-panel");
  panel.hass = {
    connection: {
      sendMessagePromise(message) {
        return new Promise((resolve, reject) => {
          const id = nextId++;
          waiting.set(id, {resolve,reject});
          socket.send(JSON.stringify({...message,id}));
        });
      }
    }
  };
  document.body.append(panel);
  window.__sidebarRealSocket = socket;
  return true;
}
"""


@pytest.mark.asyncio
@pytest.mark.parametrize("width,height", [(1366, 768), (375, 812)])
async def test_actual_ha_websocket_with_chromium_manager_ui(
    hass, hass_client, hass_access_token, width, height,
):
    """Create, disable, re-enable and delete through real HA Core WS."""
    assert await setup.async_setup_component(hass, "frontend", {})
    bootstrap = MockConfigEntry(
        domain=DOMAIN,
        title="HA Sidebar Manager",
        data={"manager_only": True},
        entry_id=f"real-browser-manager-{width}",
    )
    bootstrap.add_to_hass(hass)
    assert await hass.config_entries.async_setup(bootstrap.entry_id)
    await hass.async_block_till_done()

    # Serve HTML from the SAME real HA HTTP origin as scripts and WS.
    # Synthetic browser-fulfilled documents can be denied private-network
    # access by Chromium's Local Network Access security checks.
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/__sidebar_test_host.html",
            str(Path(__file__).with_name("host.html")),
            False,
        )
    ])
    # TestClient's server owns the actual socket and routes requests to HA.
    client = await hass_client()
    module_url = str(client.make_url("/panel_iframe_www/manager.js"))
    response = await client.get("/panel_iframe_www/manager.js")
    assert response.status == 200
    assert "ha-sidebar-manager-panel" in await response.text()
    # Verify the exact same aiohttp test server can handle a real WS upgrade.
    async with client.ws_connect("/api/websocket") as upstream_socket:
        hello = await upstream_socket.receive_json()
        assert hello["type"] == "auth_required", hello

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True, args=["--no-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": width, "height": height}
        )
        page = await context.new_page()
        page.on("console", lambda msg: print("BROWSER_CONSOLE", msg.type, msg.text))
        page.on("requestfailed", lambda req: print("BROWSER_REQUEST_FAILED", req.url, req.failure))
        page.on("websocket", lambda ws: print("BROWSER_WS_URL", ws.url))
        try:
            host_url = str(client.make_url("/__sidebar_test_host.html"))
            await page.goto(host_url)
            await page.add_script_tag(url=module_url)
            assert await page.evaluate(CONNECT, {"token": hass_access_token})

            manager = page.locator("ha-sidebar-manager-panel")
            await expect(manager.get_by_text("当前没有菜单")).to_be_visible()
            await manager.locator('button[data-action="add"]').click()
            form = manager.locator("form#editor")
            await form.locator('input[name="title"]').fill("真实连接菜单")
            await form.locator('input[name="icon"]').fill("mdi:robot")
            await form.locator('input[name="url"]').fill("/config/integrations")
            await form.locator('select[name="mode"]').select_option("3")
            await form.locator('button[type="submit"]').click()
            await expect(manager.locator(".entry strong")).to_have_text("真实连接菜单")
            entries = [
                entry for entry in hass.config_entries.async_entries(DOMAIN)
                if not entry.data.get("manager_only")
            ]
            assert len(entries) == 1
            entry = entries[0]
            assert {**entry.data, **entry.options}["url"] == "/config/integrations"

            await manager.locator('button[data-action="toggle"]').click()
            await expect(manager.locator(".entry .badge")).to_contain_text("已停用")
            await hass.async_block_till_done()
            assert entry.options["enabled"] is False

            await manager.locator('button[data-action="toggle"]').click()
            await expect(manager.locator(".entry .badge")).not_to_contain_text("已停用")
            await hass.async_block_till_done()
            assert entry.options["enabled"] is True

            page_width = await page.evaluate(
                "document.documentElement.scrollWidth"
            )
            assert page_width <= width + 2, (page_width, width)

            page.once("dialog", lambda dialog: dialog.accept())
            await manager.locator('button[data-action="delete"]').click()
            await expect(manager.locator(".entry")).to_have_count(0)
            await hass.async_block_till_done()
            assert hass.config_entries.async_get_entry(entry.entry_id) is None
        finally:
            await page.evaluate(
                "() => window.__sidebarRealSocket?.close()"
            )
            await context.close()
            await browser.close()
