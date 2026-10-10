/* Chromium browser acceptance checks for the visual manager frontend.
 * Backend WebSocket is simulated, so this does NOT test production HA.
 */
const {test, expect} = require("@playwright/test");
const path = require("node:path");
const script=path.resolve("custom_components/panel_iframe/www/manager.js");

async function mountManager(page) {
  await page.setContent('<!doctype html><html lang="zh"><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body style="margin:0;height:100vh"></body></html>');
  await page.addScriptTag({path: script});
  await page.evaluate(() => {
    window.__items = [];
    window.__calls = [];
    const p=document.createElement("ha-sidebar-manager-panel");
    p.hass={connection:{
      async sendMessagePromise(message) {
        window.__calls.push(message);
        const op=message.type.split("/").at(-1);
        if(op==="list") return window.__items.map(x=>({...x}));
        if(op==="save") {
          const eid=message.entry_id||"menu-"+(window.__items.length+1);
          const existing=window.__items.find(x=>x.entry_id===eid);
          const item={...existing,...message,entry_id:eid,menu_order:existing?.menu_order??window.__items.length};
          window.__items=window.__items.filter(x=>x.entry_id!==eid);
          window.__items.push(item);
          return {entry_id:eid};
        }
        if(op==="delete"){
          window.__items=window.__items.filter(x=>x.entry_id!==message.entry_id);
          return {deleted:true};
        }
        if(op==="reorder"){
          window.__items.sort((a,b)=>message.entry_ids.indexOf(a.entry_id)-message.entry_ids.indexOf(b.entry_id));
          window.__items.forEach((x,i)=>x.menu_order=i);
          return {saved:true};
        }
        throw new Error("Unexpected action: "+op);
      }
    }};
    document.body.appendChild(p);
  });
  return page.locator("ha-sidebar-manager-panel");
}

for(const device of [
  {name:"desktop",viewport:{width:1366,height:768}},
  {name:"mobile",viewport:{width:375,height:812}}
]){
  test.describe(device.name,()=>{
    test.use({viewport:device.viewport});

    test("create, disable, enable, edit and delete without horizontal clipping",async ({page})=>{
      page.on("dialog",dialog=>dialog.accept());
      const manager=await mountManager(page);
      await expect(manager.getByText("当前没有菜单")).toBeVisible();
      await manager.getByRole("button",{name:/新增菜单/}).click();
      const form=manager.locator("form#editor");
      await expect(form).toBeVisible();
      await form.locator('input[name="title"]').fill("自动化管理");
      await form.locator('input[name="icon"]').fill("mdi:robot");
      await form.locator('input[name="url"]').fill("/config/automation/dashboard");
      await form.locator('select[name="mode"]').selectOption("3");
      await manager.getByRole("button",{name:"保存菜单"}).click();
      await expect(manager.locator(".entry")).toHaveCount(1);
      await expect(manager.locator(".entry strong")).toHaveText("自动化管理");

      await manager.getByRole("button",{name:"停用"}).click();
      await expect(manager.locator(".entry .badge")).toContainText("已停用");
      await manager.getByRole("button",{name:"启用"}).click();
      await expect(manager.getByRole("button",{name:"停用"})).toBeVisible();

      await manager.getByRole("button",{name:"编辑"}).click();
      await form.locator('input[name="title"]').fill("设备管理");
      await manager.getByRole("button",{name:"保存菜单"}).click();
      await expect(manager.locator(".entry strong")).toHaveText("设备管理");

      const overflow=await page.evaluate(()=>{
        const panel=document.querySelector("ha-sidebar-manager-panel");
        const root=panel.shadowRoot;
        const viewport=window.innerWidth;
        const all=[...root.querySelectorAll(".main,.card,.toolbar,button,input,select,form")];
        const out=all.filter(el=>{
          const box=el.getBoundingClientRect();
          return box.width>0 && (box.right>viewport+2 || box.left<-2);
        }).map(el=>({tag:el.tagName,cls:el.className}));
        return {documentWidth:document.documentElement.scrollWidth,viewport,out};
      });
      expect(overflow.documentWidth).toBeLessThanOrEqual(overflow.viewport+2);
      expect(overflow.out).toEqual([]);

      await manager.getByRole("button",{name:"删除"}).click();
      await expect(manager.locator(".entry")).toHaveCount(0);
      await expect(manager.getByText("当前没有菜单")).toBeVisible();
    });
  });
}
