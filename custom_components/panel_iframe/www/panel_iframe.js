/* HA Sidebar Manager compatibility panel, based on MIT-licensed panel_iframe. */
(() => {
  if (customElements.get("ha-panel_iframe")) return;

  const esc = (s) => String(s ?? "").replace(/&/g, "&amp;")
    .replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  class SidebarLinkPanel extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({mode:"open"});
      this._key = null;
      this._lastNavigated = null;
      this.shadowRoot.addEventListener("click", (event) => {
        if (event.target.closest("[data-menu-toggle]")) {
          this.dispatchEvent(new CustomEvent("hass-toggle-menu", {
            bubbles:true, composed:true
          }));
        }
      });
    }

    set hass(value) { this._hass = value; }
    get hass() { return this._hass; }
    set narrow(value) { this._narrow = value; }
    get narrow() { return this._narrow; }
    set panel(value) {
      this._panel = value;
      if (this.isConnected) this._render();
    }
    get panel() { return this._panel; }

    connectedCallback() { this._render(); }

    _url(raw) {
      const text = String(raw || "").trim();
      if (/^\d+$/.test(text)) return "http://" + location.hostname + ":" + text;
      if (/^:\d+(?:\/|$)/.test(text)) return location.protocol + "//" + location.hostname + text;
      if (text.startsWith("//") || text.includes("\\")) return "";
      if (text.startsWith("/")) return text;
      try {
        const parsed = new URL(text);
        if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return "";
        return parsed.href;
      } catch {
        return "";
      }
    }

    _navigate(url) {
      if (!url.startsWith("/") || url.startsWith("//") || url.includes("\\")) return;
      if (this._lastNavigated === url) return;
      this._lastNavigated = url;
      if (location.pathname + location.search + location.hash === url) return;
      history.replaceState(null, "", url);
      this.dispatchEvent(new CustomEvent("location-changed", {
        bubbles:true, composed:true, detail:{replace:true}
      }));
    }

    _render() {
      const config = this._panel?.config || {};
      const mode = String(config.mode ?? "0");
      const url = this._url(config.url);
      const title = this._panel?.title || "侧边栏入口";
      const key = JSON.stringify([mode,url,title]);
      if (key === this._key) return;
      this._key = key;
      const style = '<style>'
        + ':host{display:block;height:100%;min-height:0;background:var(--primary-background-color);color:var(--primary-text-color);font-family:Roboto,"Noto Sans",sans-serif;}'
        + '*{box-sizing:border-box}.head{min-height:var(--header-height,56px);display:flex;align-items:center;gap:12px;padding:0 14px;background:var(--app-header-background-color,var(--card-background-color));}'
        + '.menu{border:0;background:none;font-size:22px;color:inherit;cursor:pointer;padding:8px 11px}.head h2{font-size:18px;font-weight:500;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0;}'
        + '.frame{height:calc(100% - var(--header-height,56px));}.full{height:100%;}iframe{width:100%;height:100%;border:0;}'
        + '.message{padding:24px;line-height:1.7;overflow-wrap:anywhere}.message a{color:var(--primary-color)}'
        + '.open-link{display:inline-flex;align-items:center;justify-content:center;flex:none;color:var(--primary-color);font-size:13px;font-weight:600;text-decoration:none;border:1px solid var(--divider-color);background:var(--card-background-color);border-radius:8px;min-height:36px;padding:7px 10px;white-space:nowrap}.open-link:focus-visible{outline:2px solid var(--primary-color);outline-offset:2px}.floating-actions{position:absolute;z-index:2;right:14px;bottom:18px;display:flex;gap:8px;align-items:center;max-width:calc(100% - 28px)}.floating-actions .menu,.floating-actions .open-link{background:var(--card-background-color);box-shadow:0 2px 9px #0003}'
        + '@media(min-width:760px){.floating-actions .menu{display:none}}@media(max-width:480px){.head{gap:5px;padding:0 8px}.head h2{font-size:15px}.open-link{padding:6px 8px;font-size:12px}}'
        + '</style>';
      // Browsers enforce the target's CSP/X-Frame-Options and mixed-content
      // restrictions. We must never pretend we can bypass those protections:
      // provide a safe user-visible escape hatch for every embedded mode.
      const openLink = '<a class="open-link" target="_blank" rel="noopener noreferrer" href="'
        + esc(url) + '" title="如果无法嵌入，请尝试在新窗口中打开" aria-label="在新窗口打开 '
        + esc(title) + '">新窗口打开 ↗</a>';
      const header = '<div class="head"><button class="menu" data-menu-toggle aria-label="展开侧边栏">☰</button><h2>'
        + esc(title) + '</h2>' + (url && mode === "0" ? openLink : "") + '</div>';
      let body;
      if (!url) {
        body = header + '<p class="message" role="alert">目标 URL 无效，请在侧边栏管理器中重新设置。</p>';
      } else if (mode === "3") {
        body = header + '<p class="message">正在打开 Home Assistant 内部页面…</p>';
      } else if (mode === "2" || (location.protocol === "https:" && url.startsWith("http://"))) {
        body = header + '<div class="message"><p>此页面需要在独立窗口中打开。</p>'
          + '<a target="_blank" rel="noopener noreferrer" href="' + esc(url) + '">打开 ' + esc(title) + '</a></div>';
      } else {
        const iframe = '<iframe title="' + esc(title) + '" src="' + esc(url)
          + '" allow="fullscreen" referrerpolicy="strict-origin-when-cross-origin"></iframe>';
        body = mode === "1" ? '<div class="full">' + iframe
          + '<div class="floating-actions"><button class="menu" data-menu-toggle aria-label="展开侧边栏">☰</button>'
          + openLink + '</div></div>'
          : header + '<div class="frame">' + iframe + '</div>';
      }
      this.shadowRoot.innerHTML = style + body;
      if (mode === "3" && url.startsWith("/") && !url.startsWith("//")) {
        queueMicrotask(() => {
          if (this.isConnected && this._panel?.config && this._url(this._panel.config.url) === url) {
            this._navigate(url);
          }
        });
      }
    }
  }

  customElements.define("ha-panel_iframe", SidebarLinkPanel);
})();