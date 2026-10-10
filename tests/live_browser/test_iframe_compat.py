"""Real Chromium iframe/CSP compatibility checks against HA's own HTTP server.

These tests emulate target pages' response security headers on a disposable HA
HTTP endpoint. This does *not* provide a fake Supervisor ingress service, nor
does it modify target websites' CSP or bypass iframe protection.
"""
from pathlib import Path

import pytest
from aiohttp import web
from homeassistant import setup
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from playwright.async_api import async_playwright, expect
from pytest_homeassistant_custom_component.common import MockConfigEntry


class FramePolicyFixture(HomeAssistantView):
    """Test-only response for supported / blocked iframe loads."""

    url = "/__sidebar_frame_policy/{policy}"
    name = "api:sidebar:frame_policy_test"
    requires_auth = False

    async def get(self, request, policy):
        headers = {}
        if policy == "xfo":
            headers["X-Frame-Options"] = "DENY"
        elif policy == "csp":
            headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        elif policy != "allowed":
            raise web.HTTPNotFound()
        return web.Response(
            text='<html><body><p id="frame-loaded">iframe loaded</p></body></html>',
            content_type="text/html",
            headers=headers,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["0", "1"])
@pytest.mark.parametrize("policy", ["allowed", "xfo", "csp"])
async def test_embedded_frame_has_real_browser_fallback(
    hass, hass_client, mode, policy,
):
    """Fallback link stays usable when target refuses an embedded iframe."""
    assert await setup.async_setup_component(hass, "frontend", {})
    entry = MockConfigEntry(
        domain="panel_iframe",
        title="Frame test",
        data={"manager_only": True},
        entry_id=f"iframe-bootstrap-{mode}-{policy}",
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    hass.http.register_view(FramePolicyFixture())
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/__sidebar_test_host.html",
            str(Path(__file__).with_name("host.html")), False,
        )
    ])
    client = await hass_client()
    frame_path = f"/__sidebar_frame_policy/{policy}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(viewport={"width": 375, "height": 812})
        page = await context.new_page()
        try:
            if policy in ("xfo", "csp"):
                # HA's own HTTP middleware can normalize/replace XFO headers.
                # Control only this disposable iframe response, not HA's
                # document or runtime security policy. Chromium still enforces
                # the resulting XFO/CSP rules as a real browser.
                blocked_headers = (
                    {"X-Frame-Options": "DENY"} if policy == "xfo"
                    else {"Content-Security-Policy": "frame-ancestors 'none'"}
                )
                async def blocked_response(route):
                    await route.fulfill(
                        status=200,
                        headers={"Content-Type": "text/html", **blocked_headers},
                        body='<html><body><p id="frame-loaded">iframe loaded</p></body></html>',
                    )
                await page.route(f"**{frame_path}", blocked_response)
            await page.goto(str(client.make_url("/__sidebar_test_host.html")))
            await page.add_script_tag(
                url=str(client.make_url("/panel_iframe_www/panel_iframe.js"))
            )
            await page.evaluate(
                """({url, mode}) => {
                  const panel = document.createElement("ha-panel_iframe");
                  panel.panel = {title: "Frame test", config:{url,mode}};
                  document.body.appendChild(panel);
                }""",
                {"url": frame_path, "mode": mode},
            )
            panel = page.locator("ha-panel_iframe")
            embedded = panel.locator("iframe")
            await expect(embedded).to_have_count(1)
            assert await embedded.get_attribute("src") == frame_path
            fallback = panel.locator('a.open-link[target="_blank"]')
            await expect(fallback).to_be_visible()
            assert await fallback.get_attribute("rel") == "noopener noreferrer"
            assert await fallback.get_attribute("href") == frame_path
            if policy == "allowed":
                await expect(
                    panel.frame_locator("iframe").locator("#frame-loaded")
                ).to_be_visible(timeout=10000)
            else:
                # CSP/X-Frame-Options is enforced by Chromium itself. Do not
                # try to probe a cross-origin frame or falsify header state.
                await expect(
                    panel.frame_locator("iframe").locator("#frame-loaded")
                ).to_have_count(0, timeout=10000)
            assert await page.evaluate(
                "document.documentElement.scrollWidth"
            ) <= 377
        finally:
            await context.close()
            await browser.close()
