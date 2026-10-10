/* HA Sidebar Manager - standalone management panel, MIT license. */
(() => {
  if (customElements.get("ha-sidebar-manager-panel")) return;

  const COMMAND = "panel_iframe/manager/";
  const MODES = [
    ["0", "嵌入显示"],
    ["1", "全屏显示"],
    ["2", "新窗口打开"],
    ["3", "HA 内部路径"]
  ];
  const escapeHTML = (value) => String(value ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  const STYLE = [
    ":host{display:block;height:100%;overflow:auto;background:var(--primary-background-color);color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,Roboto,'Noto Sans',sans-serif)}",
    "*{box-sizing:border-box}",
    ".top{display:flex;align-items:center;gap:12px;padding:10px 18px;background:var(--app-header-background-color,var(--card-background-color));min-height:var(--header-height,56px)}",
    ".top h1{font-size:20px;margin:0;flex:1;font-weight:600}",
    ".main{max-width:1120px;margin:0 auto;padding:24px 20px 60px}",
    ".heading{display:flex;align-items:center;gap:12px;flex-wrap:wrap;justify-content:space-between;margin-bottom:22px}",
    ".heading h2{font-size:24px;margin:0 0 5px;font-weight:700}",
    ".muted{color:var(--secondary-text-color);font-size:13px;line-height:1.6}",
    ".actions{display:flex;gap:9px;align-items:center;flex-wrap:wrap}",
    "button{border:1px solid var(--divider-color);border-radius:9px;padding:9px 12px;min-height:38px;background:var(--card-background-color);color:var(--primary-text-color);font:inherit;cursor:pointer}",
    "button:hover:not(:disabled){background:var(--secondary-background-color)}",
    "button:disabled{opacity:.4;cursor:not-allowed}",
    ".primary{background:var(--primary-color);color:white;border-color:var(--primary-color);font-weight:600}",
    ".primary:hover:not(:disabled){filter:brightness(.94);background:var(--primary-color)}",
    ".danger{color:var(--error-color,#c62828)}",
    ".entry[hidden]{display:none}.card{background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:14px;padding:17px;margin:11px 0;display:flex;align-items:center;gap:15px;min-width:0}",
    ".glyph{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;background:var(--secondary-background-color);flex:none;color:var(--primary-color)}",
    ".info{flex:1;min-width:0}",
    ".info strong{display:block;font-size:16px;margin-bottom:4px;overflow-wrap:anywhere}",
    ".target{font-size:13px;color:var(--secondary-text-color);word-break:break-all;line-height:1.6}",
    ".badge{display:inline-flex;font-size:11px;padding:3px 7px;margin-top:7px;border-radius:6px;background:var(--secondary-background-color)}",
    ".notice{padding:12px 15px;border-radius:9px;margin:12px 0;background:var(--secondary-background-color);font-size:14px;line-height:1.5}",
    ".error{border-left:4px solid var(--error-color,#d22)}",
    ".toolbar{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}",
    ".toolbar button{padding:7px 10px;min-height:33px}",
    ".search{width:min(100%,320px);padding:10px;border-radius:9px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);font:inherit}",
    "form{background:var(--card-background-color);border:1px solid var(--divider-color);padding:22px;border-radius:14px;margin-bottom:20px}",
    "form h3{margin:0 0 18px;font-size:19px}",
    ".fields{display:grid;grid-template-columns:1fr 1fr;gap:16px}",
    "label{display:block;font-size:14px;font-weight:600;margin-bottom:7px}",
    "input,select{width:100%;min-height:41px;border:1px solid var(--divider-color);background:var(--primary-background-color);color:var(--primary-text-color);border-radius:8px;padding:9px 10px;font:inherit}",
    ".fullfield{grid-column:1/-1}",
    ".check{display:flex;align-items:center;gap:9px;font-weight:400}",
    ".check input{width:auto;min-height:auto}",
    ".form-actions{margin-top:18px;display:flex;gap:10px;justify-content:flex-end}",
    ".empty{text-align:center;background:var(--card-background-color);border-radius:14px;padding:50px 20px;color:var(--secondary-text-color)}",
    "@media(max-width:760px){.main{padding:15px 12px 55px}.card{align-items:flex-start;flex-wrap:wrap}.toolbar{width:100%;justify-content:flex-start;padding-left:58px}.fields{grid-template-columns:1fr}.fullfield{grid-column:1}.heading h2{font-size:21px}}"
  ].join("\n");

  class SidebarManager extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({mode:"open"});
      this._entries = [];
      this._busy = false;
      this._loaded = false;
      this._error = "";
      this._notice = "";
      this._showForm = false;
      this._editing = null;
      this._draft = null;
      this._search = "";
      this.shadowRoot.addEventListener("click", (event) => this._onClick(event));
      this.shadowRoot.addEventListener("submit", (event) => this._onSubmit(event));
      this.shadowRoot.addEventListener("input", (event) => {
        if (event.target.id !== "filter") return;
        this._search = event.target.value;
        this.shadowRoot.querySelectorAll(".entry").forEach((element) => {
          element.hidden = !element.dataset.search.includes(this._search.trim().toLowerCase());
        });
      });
    }

    set hass(value) {
      this._hass = value;
      if (this.isConnected && !this._loaded && !this._busy) this._refresh();
    }
    get hass() { return this._hass; }
    set panel(value) { this._panel = value; }
    get panel() { return this._panel; }
    set narrow(value) { this._narrow = value; }
    get narrow() { return this._narrow; }

    connectedCallback() {
      this._render();
      if (this._hass && !this._loaded) this._refresh();
    }

    async _send(action, fields={}) {
      if (!this._hass?.connection) throw new Error("尚未连接 Home Assistant");
      return await this._hass.connection.sendMessagePromise({
        type: COMMAND + action, ...fields
      });
    }

    async _refresh() {
      if (this._busy) return;
      this._busy = true;
      this._render();
      try {
        this._entries = await this._send("list");
        this._loaded = true;
        this._error = "";
      } catch (error) {
        this._error = "读取侧边栏配置失败：" + (error?.message || String(error));
      } finally {
        this._busy = false;
        this._render();
      }
    }

    _formHTML() {
      if (!this._showForm) return "";
      const item = this._draft || this._editing || {};
      const selected = String(item.mode ?? "3");
      return '<form id="editor"><h3>' + (item.entry_id ? "编辑菜单" : "新增菜单") + '</h3>'
        + '<div class="fields"><div><label for="title">显示名称</label>'
        + '<input id="title" name="title" maxlength="100" required placeholder="例如：自动化管理" value="' + escapeHTML(item.title || "") + '"></div>'
        + '<div><label for="icon">MDI 图标</label><input id="icon" name="icon" required placeholder="mdi:robot" value="'
        + escapeHTML(item.icon || "mdi:link-box-outline") + '"></div>'
        + '<div class="fullfield"><label for="url">目标路径或 URL</label><input id="url" name="url" required placeholder="/config/automation/dashboard 或 https://..." value="'
        + escapeHTML(item.url || "") + '"><p class="muted">HA 内部页面填写 / 开头的相对路径；外部站点需允许浏览器嵌入。</p></div>'
        + '<div><label for="mode">打开模式</label><select id="mode" name="mode">'
        + MODES.map(([value,label]) => '<option value="' + value + '"' + (value === selected ? " selected" : "") + '>' + label + '</option>').join("")
        + '</select></div>'
        + '<div><label>访问限制</label><label class="check"><input type="checkbox" name="require_admin"'
        + (item.require_admin ? " checked" : "") + '>仅管理员可见</label></div>'
        + '<div><label>菜单状态</label><label class="check"><input type="checkbox" name="enabled"'
        + (item.enabled !== false ? " checked" : "") + '>启用菜单</label></div></div>'
        + '<div class="form-actions"><button type="button" data-action="cancel">取消</button>'
        + '<button class="primary" type="submit"' + (this._busy ? " disabled" : "") + '>保存菜单</button></div></form>';
    }

    _entryHTML(item,index) {
      const mode = MODES.find(pair => pair[0] === String(item.mode))?.[1] || "未知模式";
      const target = item.url || "尚未配置目标路径";
      const search = (item.title + " " + target).toLowerCase();
      const visible = search.includes(this._search.trim().toLowerCase());
      return '<div class="card entry" data-search="' + escapeHTML(search) + '"' + (visible ? "" : " hidden") + '>'
        + '<div class="glyph"><ha-icon icon="' + escapeHTML(item.icon) + '"></ha-icon></div>'
        + '<div class="info"><strong>' + escapeHTML(item.title) + '</strong><div class="target">' + escapeHTML(target) + '</div>'
        + '<span class="badge">' + escapeHTML(mode) + (item.require_admin ? " · 管理员" : "") + (item.enabled === false ? " · 已停用" : "") + '</span></div>'
        + '<div class="toolbar">'
        + '<button type="button" data-action="up" data-id="' + escapeHTML(item.entry_id) + '"' + (index === 0 ? " disabled" : "") + ' aria-label="上移">↑</button>'
        + '<button type="button" data-action="down" data-id="' + escapeHTML(item.entry_id) + '"' + (index === this._entries.length-1 ? " disabled" : "") + ' aria-label="下移">↓</button>'
        + '<button type="button" data-action="toggle" data-id="' + escapeHTML(item.entry_id) + '">' + (item.enabled === false ? "启用" : "停用") + '</button>'
        + '<button type="button" data-action="edit" data-id="' + escapeHTML(item.entry_id) + '">编辑</button>'
        + '<button type="button" class="danger" data-action="delete" data-id="' + escapeHTML(item.entry_id) + '">删除</button>'
        + '</div></div>';
    }

    _render() {
      const loading = this._busy ? '<div class="notice">正在处理，请稍候…</div>' : "";
      const error = this._error ? '<div class="notice error" role="alert">' + escapeHTML(this._error) + '</div>' : "";
      const notice = this._notice ? '<div class="notice" role="status">' + escapeHTML(this._notice) + '</div>' : "";
      this.shadowRoot.innerHTML = '<style>' + STYLE + '</style>'
        + '<header class="top"><ha-menu-button></ha-menu-button><h1>侧边栏管理器</h1></header>'
        + '<div class="main"><div class="heading"><div><h2>菜单管理</h2>'
        + '<div class="muted">管理 Home Assistant 内部页面、集成入口及外部网页 · ' + this._entries.length + ' 项</div></div>'
        + '<div class="actions"><button data-action="refresh">刷新</button><button class="primary" data-action="add">＋ 新增菜单</button></div></div>'
        + error + notice + loading + this._formHTML()
        + '<div class="actions"><input class="search" id="filter" type="search" aria-label="搜索菜单" placeholder="搜索菜单或路径…" value="' + escapeHTML(this._search) + '"></div>'
        + (this._entries.length ? this._entries.map((item,index) => this._entryHTML(item,index)).join("")
           : '<div class="empty">当前没有菜单，点击“新增菜单”开始配置。</div>')
        + '<p class="muted">提示：↑↓ 调整的是管理器中的配置顺序。HA 左侧栏的实际顺序仍可能受每位用户自己的排序设置影响。</p>'
        + '</div>';
      const menu = this.shadowRoot.querySelector("ha-menu-button");
      if (menu) { menu.hass = this._hass; menu.narrow = this._narrow; }
    }

    async _onClick(event) {
      const button = event.target.closest("button[data-action]");
      if (!button || this._busy) return;
      const action = button.dataset.action;
      const entryId = button.dataset.id;
      if (action === "refresh") return this._refresh();
      if (action === "add") {
        this._editing = null;
        this._draft = null;
        this._showForm = true;
        this._error = "";
        return this._render();
      }
      if (action === "cancel") {
        this._showForm = false;
        this._editing = null;
        this._draft = null;
        return this._render();
      }
      if (action === "edit") {
        this._editing = this._entries.find(item => item.entry_id === entryId);
        this._draft = null;
        this._showForm = Boolean(this._editing);
        return this._render();
      }
      if (action === "toggle") {
        const item = this._entries.find(row => row.entry_id === entryId);
        if (!item) return;
        return this._mutate("save", {
          entry_id: item.entry_id,
          title: item.title,
          url: item.url,
          icon: item.icon,
          mode: String(item.mode),
          require_admin: Boolean(item.require_admin),
          enabled: item.enabled === false,
        }, item.enabled === false ? "菜单已启用" : "菜单已停用");
      }
      if (action === "delete") {
        const item = this._entries.find(row => row.entry_id === entryId);
        if (!item || !confirm('确认删除菜单“' + item.title + '”？此操作也会删除对应的 HA 集成配置记录。')) return;
        return this._mutate("delete", {entry_id: entryId}, "菜单已删除");
      }
      if (action === "up" || action === "down") {
        const index = this._entries.findIndex(item => item.entry_id === entryId);
        const to = index + (action === "up" ? -1 : 1);
        if (index < 0 || to < 0 || to >= this._entries.length) return;
        const ids = this._entries.map(item => item.entry_id);
        [ids[index], ids[to]] = [ids[to], ids[index]];
        return this._mutate("reorder", {entry_ids: ids}, "管理列表顺序已保存");
      }
    }

    async _onSubmit(event) {
      if (event.target.id !== "editor") return;
      event.preventDefault();
      if (this._busy) return;
      const form = event.target;
      const fields = new FormData(form);
      const payload = {
        title: String(fields.get("title") || "").trim(),
        icon: String(fields.get("icon") || "").trim(),
        url: String(fields.get("url") || "").trim(),
        mode: String(fields.get("mode") || "3"),
        require_admin: form.elements.namedItem("require_admin").checked,
        enabled: form.elements.namedItem("enabled").checked
      };
      if (this._editing?.entry_id) payload.entry_id = this._editing.entry_id;
      this._draft = payload;
      await this._mutate("save", payload, "菜单已保存");
    }

    async _mutate(action, payload, notice) {
      this._busy = true;
      this._error = "";
      this._notice = "";
      this._render();
      try {
        await this._send(action, payload);
        this._showForm = false;
        this._editing = null;
        this._draft = null;
        this._entries = await this._send("list");
        this._loaded = true;
        this._notice = notice;
      } catch (error) {
        this._error = "操作失败：" + (error?.message || String(error));
      } finally {
        this._busy = false;
        this._render();
      }
    }
  }

  customElements.define("ha-sidebar-manager-panel", SidebarManager);
})();