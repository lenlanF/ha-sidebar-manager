# Chromium + real HA WebSocket browser validation

**Unreleased development:** v0.1.0-dev.8, HA Core 2026.10, Python 3.14, Playwright Chromium.

## Architecture

The isolated `live-ha-websocket-chromium` CI job launches the Home Assistant Core test runtime with the fork installed under the legacy `panel_iframe` domain. It registers a test-only static route for `tests/live_browser/host.html` so Chromium begins on a real same-origin Home Assistant HTTP page, with explicit UTF-8.

The browser fetches `/panel_iframe_www/manager.js` from **HA HTTP**, authenticates via native browser `WebSocket` to **HA `/api/websocket`**, and uses a minimal JavaScript implementation of `hass.connection.sendMessagePromise` to deliver real menu commands. There are **no fabricated backend response handlers** in this suite.

The test verifies HA's real `ConfigEntry` state for create, edit, disable, enable, and delete on desktop (1366×768) and mobile-width (375×812). It also asserts absence of overall document horizontal overflow.

## Reproduce

Install Python 3.14, Home Assistant Core 2026.10, `home-assistant-frontend==20260930.2`, `pytest-homeassistant-custom-component`, and `playwright`. Then:

```bash
python -m playwright install --with-deps chromium
PYTEST_ADDOPTS=--asyncio-mode=auto python -m pytest -q tests/live_browser -x
```

On Windows PowerShell, set the environment variable using `$env:PYTEST_ADDOPTS="--asyncio-mode=auto"` before running pytest.

## Evidence

- [Source checks: all jobs succeeded](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38059902505): real HA WebSocket Chromium **2/2 passed**, HA Core functional **19 passed**, prior mocked browser tests, source/isolated, API smoke, upstream source swap/rollback and native storage cold-load passed.
- [HACS validation 9/9](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38059902424).

## Diagnosed and fixed test harness issues

The first integration browser attempt passed a full URL into aiohttp's relative-path `TestClient.get`. Next, navigating directly to JavaScript before injecting HTML caused incorrect browser character encoding. A synthetic Playwright-fulfilled HTML origin then triggered **Chromium 153 `ERR_BLOCKED_BY_LOCAL_NETWORK_ACCESS_CHECKS`** for a loopback WebSocket. Rather than disabling browser protection, the final fixture served UTF-8 HTML from the actual HA test HTTP server. The browser then connected to the real HA WebSocket successfully.

The test also learned that newly created menu settings may live in `ConfigEntry.data`, while original upstream settings live in `options`, so effective config is checked by merging both.

## Important limitations

- The test does **not** launch the complete logged-in Home Assistant SPA/navigation shell; the browser host is minimal and `hass.connection` is a lightweight adapter.
- It does **not** check HACS repo switching for installed integrations, physical mobile apps, Supervisor/HAOS restart, full server backups, or add-on Ingress/CSP compatibility.
- Nothing in this suite modifies a production HA instance. Do not infer a production-ready release from this check alone.

## Extended HA frontend registry and permission validation (v0.1.0-dev.9)

The browser suite now additionally calls Home Assistant's **real authenticated frontend `get_panels` WebSocket command**, once as a HA administrator and once as a read-only HA user, at two Chromium viewport sizes. It validates manager/admin-only panel visibility, unrestricted menu visibility, component metadata and module URLs, then loads and executes the menu component by the module URL supplied by HA. It also checks `noopener noreferrer` on new-window links.

The registered `/ha-sidebar-manager` and menu URL paths are checked against Home Assistant's genuine SPA index responder, and a menu unload must immediately disappear from `get_panels`. The test uses the HA-served minimal host for its JS component rather than a complete logged-in HA frontend shell; no client-side responses are mocked.

- [Source CI](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38061488602): **4/4 real HA-WebSocket Chromium tests passed**; 19 HA Core functional tests plus existing regression jobs also passed.
- [HACS validator](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38061488639): **9/9 passed**.

Remaining: complete logged-in HA navigation shell, HACS repo switching and real deployment rollback, physical mobile and Ingress/CSP.
