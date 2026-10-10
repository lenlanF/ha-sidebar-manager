"""Full Home Assistant SPA smoke test using the real authentication bootstrap.

Unlike test_browser_real_ha.py this navigates the *actual* frontend shell and
lets HA itself instantiate the custom sidebar manager from get_panels. The
auth token is injected in a disposable browser context only, never saved.
"""
import json

import pytest
from homeassistant import setup
from playwright.async_api import async_playwright, expect
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "panel_iframe"


@pytest.mark.asyncio
@pytest.mark.parametrize("width,height", [(1366, 768), (375, 812)])
async def test_full_ha_frontend_shell_opens_sidebar_manager(
    hass, hass_client, hass_access_token, width, height,
):
    """Start Home Assistant's actual SPA at its registered manager URL."""
    assert await setup.async_setup_component(hass, "frontend", {})
    bootstrap = MockConfigEntry(
        domain=DOMAIN, title="HA Sidebar Manager",
        data={"manager_only": True}, entry_id=f"shell-bootstrap-{width}",
    )
    bootstrap.add_to_hass(hass)
    assert await hass.config_entries.async_setup(bootstrap.entry_id)
    await hass.async_block_till_done()
    client = await hass_client()
    url = str(client.make_url("/ha-sidebar-manager"))
    origin = str(client.make_url("/")).rstrip("/")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(viewport={"width": width, "height": height})
        # Python Playwright's add_init_script accepts a script, not args.
        # Serialize only in memory; do not log token-bearing browser state.
        credentials = json.dumps(
            {"origin": origin, "accessToken": hass_access_token}
        )
        await context.add_init_script(script="""
          (() => {
            const {origin, accessToken} = """ + credentials + """;
            if (location.origin !== origin) return;
            localStorage.setItem("hassTokens", JSON.stringify({
              hassUrl: origin,
              clientId: origin + "/",
              expires: Date.now() + 25 * 60 * 1000,
              refresh_token: "",
              access_token: accessToken,
              expires_in: 1800
            }));
          })();
        """)
        page = await context.new_page()
        try:
            response = await page.goto(url, wait_until="domcontentloaded")
            assert response and response.status == 200
            await expect(page.locator("ha-sidebar-manager-panel")).to_be_visible(
                timeout=45000
            )
            manager = page.locator("ha-sidebar-manager-panel")
            await expect(manager.get_by_text("侧边栏管理器")).to_be_visible()
            await expect(manager.get_by_text("当前没有菜单")).to_be_visible()
            # The actual HA shell must attach a connection, not the test
            # adapter used by the previous live-browser suite.
            assert await manager.evaluate(
                "(el) => Boolean(el.hass?.connection?.sendMessagePromise)"
            )
            await manager.locator('button[data-action="add"]').click()
            form = manager.locator("form#editor")
            await form.locator('input[name="title"]').fill("完整前端菜单")
            await form.locator('input[name="url"]').fill("/config/integrations")
            await form.locator('input[name="icon"]').fill("mdi:devices")
            await form.locator('select[name="mode"]').select_option("3")
            await form.locator('button[type="submit"]').click()
            await expect(manager.locator(".entry strong")).to_have_text("完整前端菜单")
            entries = [
                row for row in hass.config_entries.async_entries(DOMAIN)
                if not row.data.get("manager_only")
            ]
            assert len(entries) == 1 and entries[0].title == "完整前端菜单"
            width_actual = await page.evaluate(
                "document.documentElement.scrollWidth"
            )
            assert width_actual <= width + 2
        finally:
            await context.close()
            await browser.close()
