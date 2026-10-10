# Ingress、iframe 与浏览器安全限制

> 适用范围：HA Sidebar Manager 开发分支。此插件不提供代理服务器、不签发 Supervisor Ingress 令牌，也不能绕过浏览器安全头。

## 菜单打开模式

| 模式 | 行为 | 建议用途 |
| --- | --- | --- |
| 0 嵌入显示 | 显示菜单标题栏、iframe 和「新窗口打开」 | 允许 iframe 的网站与现有同源页面 |
| 1 全屏显示 | iframe 占据可用区域；右下提供菜单按钮和「新窗口打开」 | 仪表盘与自托管应用 |
| 2 新窗口打开 | 只显示安全新窗口链接，不嵌入 | 拒绝 iframe 的网站 |
| 3 HA 内部路径 | 不渲染 iframe，发出 HA 前端内部路由跳转事件 | HA 已注册的内部路径、部分原生应用入口 |

模式 0/1 只能嵌入目标网站**允许**的内容。遇到 CSP `frame-ancestors`、`X-Frame-Options` 或反向代理限制时，浏览器会阻止 iframe；目标站点的拒绝行为不是菜单加载器能够合法解除的。

**改进：** 模式 0/1 现在都保留一个始终可见、键盘可访问的「新窗口打开」链接（`target="_blank"` + `rel="noopener noreferrer"`），用于嵌入失败时由用户主动打开。这不是自动判断嵌入结果；跨域 iframe 的真实状态不应被前端探测或伪装为成功。

如果 HA 本身通过 HTTPS 访问，而目标仅提供 HTTP，当前插件不会强制加载混合内容 iframe，而会显示新窗口选项。新窗口能否访问受浏览器、网络和目标服务的协议支持影响。

## 附加组件 Ingress

Supervisor/HAOS 的 Ingress 是独立的认证及路径转发能力。一个支持 Ingress 的附加组件可能通过 HA 前端注册自己的入口，也可能使用短期的 `/api/hassio_ingress/...` 路径。

- **优先**使用 HA 自己已经注册的附加组件导航入口或内部路由，按模式 3 配置；先手工确认该路径在当前 HA 实例与用户权限下有效。不要凭附加组件 slug 猜测可用 URL。
- 不要复制、导出、公开分享可能带有 Ingress token 的临时路径。菜单的 JSON 备份会包含 URL，务必确认没有敏感令牌。
- 如必须嵌入附加组件的页面，需在真实 HAOS + Supervisor + 对应附加组件中检查其 iframe / WebSocket / 路径策略。仅装有 Home Assistant Core 的 CI 不具备 Supervisor Ingress 服务，**不能宣称 Ingress 已经过端到端测试**。
- 不建议通过删除 `X-Frame-Options`、无条件放宽 CSP 或公开容器端口来“修复”嵌入失败。应优先使用附加组件的受支持入口。

官方参考：[Home Assistant 应用 Ingress 开发文档](https://developers.home-assistant.io/docs/apps/presentation/)；[Custom panel 选项](https://www.home-assistant.io/integrations/panel_custom/)。

## 2026.10 Chromium 自动化覆盖

测试文件：

- `tests/live_browser/test_iframe_compat.py`：HA HTTP 测试服务器提供允许 iframe、`X-Frame-Options: DENY`、`Content-Security-Policy: frame-ancestors 'none'` 三类响应；在真实 Chromium 中验证浏览器拦截、按钮可见、链接目标与 `noopener noreferrer`，并覆盖模式 0 和 1。
- `tests/live_browser/test_full_frontend_shell.py`：从已认证的完整 HA 前端打开菜单入口，验证模式 3 能够发起内部路径跳转。
- `tests/test_frontend_panel.cjs`：验证组件在没有完整 HA 的 JS 单元环境下仍保持正确 URL、内部导航和安全新窗口链接。

测试使用**受控本地响应**而不是外部站点或真正的 Supervisor；它只能证明当前前端行为与浏览器安全头兼容，不能证明所有第三方网站或所有附加组件都能嵌入。

## 在独立 HAOS 测试机上的验收清单

1. 先创建完整 HA 备份并保留旧版插件来源，测试机而非生产环境操作。
2. 验证 HA HTTP 与 HTTPS（若有）、局域网访问及远程访问的页面链接。
3. 使用允许 iframe 的 HTTPS 页面验证模式 0、1；再使用故意禁止 iframe 的页面确认新窗口入口可见。
4. 对支持 Ingress 的每个附加组件，从 **HA 官方入口**进入，确认 URL、登录权限、WebSocket、资源加载和返回菜单行为；再验证插件的模式 3 路由。
5. 检查不同用户、管理员权限、PC 与手机宽度，确认敏感页面未因菜单可见性配置而扩大权限。
6. 复核 HA 日志和浏览器控制台；出现失败时记录目标网址的**脱敏形式**、响应的 CSP/X-Frame-Options 与场景，切勿在工单公开 token。

未在 HAOS/Supervisor 环境完成以上实际测试前，Ingress 兼容性保持「待验收」，不得用 Core CI 的通过结果代替。
