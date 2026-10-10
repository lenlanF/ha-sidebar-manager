/* Simulated DOM regression for the visual Home Assistant sidebar manager.
 * This is not a substitute for a real HA browser or mobile acceptance test.
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { JSDOM } = require("jsdom");

async function main() {
  const dom = new JSDOM("<!doctype html><html><body></body></html>", {
    url: "https://ha.example/",
    runScripts: "outside-only",
    pretendToBeVisual: true,
  });
  const win = dom.window;
  win.confirm = () => true;
  win.eval(fs.readFileSync("custom_components/panel_iframe/www/manager.js", "utf8"));
  const Manager = win.customElements.get("ha-sidebar-manager-panel");
  assert.ok(Manager, "management panel must be a registered custom element");

  let entries = [];
  let failSave = false;
  const requests = [];
  const connection = {
    async sendMessagePromise(message) {
      requests.push(message);
      const action = message.type.replace("panel_iframe/manager/", "");
      if (action === "list") return entries.map((row) => ({...row}));
      if (action === "save") {
        if (failSave) throw new Error("simulated network failure");
        const id = message.entry_id || "entry-" + (entries.length + 1);
        const previous = entries.find((row) => row.entry_id === id);
        const next = {
          ...previous,
          ...message,
          entry_id: id,
          menu_order: previous?.menu_order || entries.length,
        };
        entries = entries.filter((row) => row.entry_id !== id).concat([next]);
        return {entry_id: id};
      }
      if (action === "delete") {
        entries = entries.filter((row) => row.entry_id !== message.entry_id);
        return {deleted: true};
      }
      if (action === "reorder") {
        entries.sort((a,b) => message.entry_ids.indexOf(a.entry_id) -
                              message.entry_ids.indexOf(b.entry_id));
        entries.forEach((row,i) => {row.menu_order = i;});
        return {saved: true};
      }
      throw Error("unexpected action " + action);
    },
  };
  const ui = new Manager();
  win.document.body.appendChild(ui);
  ui.hass = {connection};
  const tick = async () => {
    for(let n=0;n<5;n++) await new Promise((resolve)=>setTimeout(resolve,0));
  };
  const button = (action) => ui.shadowRoot.querySelector('button[data-action="' + action + '"]');
  await tick();
  assert.ok(ui.shadowRoot.textContent.includes("当前没有菜单"));
  assert.ok(requests.some((msg) => msg.type.endsWith("/list")));

  button("add").click();
  const form = ui.shadowRoot.querySelector("form#editor");
  assert.ok(form,"add action must open native form");
  form.elements.namedItem("title").value = "自动化管理";
  form.elements.namedItem("url").value = "/config/automation/dashboard";
  form.elements.namedItem("icon").value = "mdi:robot";
  form.elements.namedItem("mode").value = "3";
  form.elements.namedItem("require_admin").checked = true;
  form.dispatchEvent(new win.Event("submit", {bubbles:true,cancelable:true}));
  await tick();
  assert.equal(entries.length, 1);
  assert.equal(entries[0].title, "自动化管理");
  assert.equal(entries[0].require_admin, true);
  assert.equal(ui.shadowRoot.querySelectorAll(".entry").length,1);

  button("toggle").click();
  await tick();
  assert.equal(entries[0].enabled, false, "disabling persists state");
  assert.ok(ui.shadowRoot.textContent.includes("已停用"));
  button("toggle").click();
  await tick();
  assert.equal(entries[0].enabled, true, "re-enabling restores state");

  button("edit").click();
  const editor = ui.shadowRoot.querySelector("form");
  editor.elements.namedItem("title").value = "新自动化";
  editor.dispatchEvent(new win.Event("submit", {bubbles:true,cancelable:true}));
  await tick();
  assert.equal(entries[0].title,"新自动化");

  // On a failed save, keep the user's draft available rather than clearing it.
  failSave = true;
  button("edit").click();
  const failing = ui.shadowRoot.querySelector("form");
  failing.elements.namedItem("title").value = "保存失败保留";
  failing.dispatchEvent(new win.Event("submit", {bubbles:true,cancelable:true}));
  await tick();
  assert.ok(ui.shadowRoot.textContent.includes("操作失败"));
  assert.equal(ui.shadowRoot.querySelector("#title").value, "保存失败保留");
  failSave = false;
  button("cancel").click();

  button("delete").click();
  await tick();
  assert.equal(entries.length,0);
  assert.ok(ui.shadowRoot.textContent.includes("当前没有菜单"));

  // User-controlled strings are escaped before insertion in the DOM.
  entries = [{
    entry_id:"malicious", title:'<img src=x onerror=alert(1)>',
    url:"/config/integrations", mode:"3", icon:"mdi:robot",
    require_admin:false,menu_order:0,
  }];
  button("refresh").click();
  await tick();
  assert.equal(ui.shadowRoot.querySelector(".entry img"), null);
  assert.ok(ui.shadowRoot.querySelector(".entry strong").textContent.includes("<img"));

  // The original integration can leave title-only entries without a URL.
  // They should stay editable, but new menus must still require a target.
  entries = [{
    entry_id:"legacy-empty", title:"未配置旧菜单", url:"",
    icon:"mdi:link", mode:"0", require_admin:false,
    enabled:true, menu_order:0,
  }];
  button("refresh").click();
  await tick();
  button("edit").click();
  assert.equal(ui.shadowRoot.querySelector("#url").required, false,
    "editing a legacy unconfigured entry must not require a URL");
  ui.shadowRoot.querySelector("#title").value = "重命名未配置菜单";
  ui.shadowRoot.querySelector("form").dispatchEvent(
    new win.Event("submit", {bubbles:true,cancelable:true})
  );
  await tick();
  assert.equal(entries[0].title, "重命名未配置菜单");
  assert.equal(entries[0].url, "");
  button("add").click();
  assert.equal(ui.shadowRoot.querySelector("#url").required, true,
    "creating a new menu must require a URL");
  button("cancel").click();

  win.close();
  console.log("Visual manager DOM create/edit/delete/failure/escaping: OK");
}
main().catch((err)=>{console.error(err);process.exitCode=1;});
