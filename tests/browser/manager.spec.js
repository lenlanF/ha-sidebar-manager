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
        if(op==="backup") return {
          format: "ha-sidebar-manager",version:1,
          exported_at:new Date().toISOString(),
          items:window.__items.map(x=>({
            entry_id:x.entry_id,title:x.title,url:x.url,icon:x.icon,
            mode:x.mode,require_admin:x.require_admin,enabled:x.enabled,
            menu_order:x.menu_order,
          })),
        };
        if(op==="restore"){
          const plan=message.backup.items.map((record,index)=>({
            index,title:record.title,entry_id:record.entry_id,
            action:window.__items.some(x=>x.entry_id===record.entry_id)
              ? "update":"create",
          }));
          const counts={create:plan.filter(x=>x.action==="create").length,
            update:plan.filter(x=>x.action==="update").length,skip:0};
          if(!message.apply)return {plan,counts,applied:false};
          for(const record of message.backup.items){
            window.__items=window.__items.filter(x=>x.entry_id!==record.entry_id);
            window.__items.push({...record});
          }
          return {applied:true,partial:false,counts,completed:plan};
        }

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
      // Download a local JSON snapshot, alter a menu, then restore from it.
      const downloadEvent=page.waitForEvent("download");
      await manager.getByRole("button",{name:"导出备份"}).click();
      const download=await downloadEvent;
      expect(download.suggestedFilename()).toMatch(/^ha-sidebar-manager-.*\.json$/);
      const saved=require("node:fs").readFileSync(await download.path());
      const parsed=JSON.parse(saved.toString("utf8"));
      expect(parsed.items[0].title).toBe("设备管理");

      await manager.getByRole("button",{name:"编辑"}).click();
      await form.locator('input[name="url"]').fill("/config/logs");
      await manager.getByRole("button",{name:"保存菜单"}).click();
      await expect(manager.locator(".entry .target")).toHaveText("/config/logs");

      await manager.locator("#import-backup-file").setInputFiles({
        name:"sidebar-backup.json",mimeType:"application/json",buffer:saved,
      });
      await expect(manager.getByText("导入预览（尚未修改）")).toBeVisible();
      await expect(manager.getByText("新增 0 项，更新 1 项，跳过 0 项。",{exact:false})).toBeVisible();
      // Preview must not write until the user explicitly confirms.
      await expect(manager.locator(".entry .target")).toHaveText("/config/logs");
      await manager.getByRole("button",{name:"确认恢复菜单"}).click();
      await expect(manager.locator(".entry .target")).toHaveText("/config/automation/dashboard");


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
