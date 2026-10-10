/* HA Sidebar Manager - compatibility panel. Upstream MIT: shaonianzhentan. */
customElements.whenDefined("ha-panel-lovelace").then(() => {
  if (customElements.get("ha-panel_iframe")) return;
  const LitElement = Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
  const html = LitElement.prototype.html;
  const css = LitElement.prototype.css;

  class SidebarPanel extends LitElement {
    static properties = { panel: {}, hass: {}, narrow: {} };

    static styles = css`
      :host { display:block; height:100%; min-height:0; background:var(--primary-background-color); }
      .toolbar { height:var(--header-height,56px); box-sizing:border-box; display:flex;
        align-items:center; gap:12px; padding:0 12px; color:var(--primary-text-color);
        background:var(--app-header-background-color,var(--card-background-color)); }
      .title { font-size:18px; flex:1; }
      .content { height:calc(100% - var(--header-height,56px)); }
      iframe { width:100%; height:100%; border:0; }
      .message { padding:24px; line-height:1.7; }
      a { color:var(--primary-color); }
      .full { height:100%; }
    `;

    _mode() { return String(this.panel?.config?.mode ?? "0"); }

    _url() {
      const raw = String(this.panel?.config?.url ?? "").trim();
      if (/^\d+$/.test(raw)) return `http://${location.hostname}:${raw}`;
      if (/^:\d+(?:\/|$)/.test(raw)) return `${location.protocol}//${location.hostname}${raw}`;
      if (raw.startsWith("//")) return ""; // Disallow ambiguous protocol-relative targets.
      if (raw.startsWith("/")) return raw;
      try {
        const url = new URL(raw);
        return ["http:", "https:"].includes(url.protocol) ? url.href : "";
      } catch { return ""; }
    }

    _isInternalRoute(url) {
      return url.startsWith("/") && !url.startsWith("//") && !url.includes("\\");
    }

    _emit(type, detail) {
      this.dispatchEvent(new CustomEvent(type, { bubbles:true, composed:true, detail }));
    }

    updated() {
      if (this._mode() !== "3") return;
      const target = this._url();
      if (!this._isInternalRoute(target)) return;
      if (this._lastNavigated === target) return;
      this._lastNavigated = target;
      if (location.pathname + location.search + location.hash !== target) {
        history.replaceState(null, "", target);
        this._emit("location-changed", { replace:true });
      }
    }

    render() {
      const mode = this._mode();
      const url = this._url();
      const title = this.panel?.title ?? "侧边栏";
      const toolbar = html`<div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <span class="title">${title}</span>
      </div>`;
      if (!url) return html`${toolbar}<p class="message">链接无效，请在集成选项中修改 URL。</p>`;
      if (mode === "3") {
        if (!this._isInternalRoute(url)) return html`${toolbar}<p class="message">内部页面模式只支持 HA 本站路径。</p>`;
        return html`${toolbar}<p class="message">正在打开内部页面…</p>`;
      }
      if (mode === "2") {
        return html`${toolbar}<div class="message">
          <p>该入口设置为新窗口打开。为了避免浏览器阻止弹窗，请点击下面的链接：</p>
          <a href="${url}" target="_blank" rel="noopener noreferrer">打开 ${title}</a>
        </div>`;
      }
      if (location.protocol === "https:" && url.startsWith("http://")) {
        return html`${toolbar}<div class="message">
          <p>HTTPS 页面通常不能嵌入 HTTP 站点。请通过以下链接直接打开：</p>
          <a href="${url}" target="_blank" rel="noopener noreferrer">打开 ${title}</a>
        </div>`;
      }
      const frame = html`<iframe src="${url}" title="${title}" allow="fullscreen" referrerpolicy="strict-origin-when-cross-origin"></iframe>`;
      return mode === "1" ? html`<div class="full">${frame}</div>`
        : html`${toolbar}<div class="content">${frame}</div>`;
    }
  }
  customElements.define("ha-panel_iframe", SidebarPanel);
});
