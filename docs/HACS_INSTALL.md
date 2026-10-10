# HA Sidebar Manager v0.1.0 — HACS 正式版安装

> 2026-10-11 首个正式版。最低 Home Assistant 2026.10.0。用户初步测试没有发现明显问题，但并不代表已在所有 HAOS/Supervisor 环境全面验收。

## 新用户直接安装

1. Home Assistant → **HACS → ⋮ → 自定义存储库**。
2. 仓库地址：`https://github.com/lenlanF/ha-sidebar-manager`；类别 **Integration**。
3. 在 HACS 搜索 **HA Sidebar Manager**，下载正式 `v0.1.0`。如果 GitHub Release 尚未生成，HACS 可能使用 `main`；请核实安装文件 `manifest.json` 中的版本为 `0.1.0`。
4. 重启 Home Assistant；进入「设置 → 设备与服务 → 添加集成」，搜索 **HA Sidebar Manager** 并选择「安装侧边栏管理器」。
5. 使用管理员账号打开「侧边栏管理」或访问 `/ha-sidebar-manager`；新增一个内部地址例如 `/config/integrations`、模式 3，检验启停、编辑、删除和重启后保留设置。

## 如果原来已经通过 HACS 安装 shaonianzhentan/panel_iframe

新旧项目的 HA 集成域和安装目录均为 `panel_iframe`。**不能让两个 HACS 仓库同时管理相同的 `/config/custom_components/panel_iframe/` 文件。**

- 首先创建 HAOS **完整备份**，保存到其他设备。再记录原 HACS 仓库来源及版本、菜单名称和入口 URL。
- 切换时应只解除/卸载旧 HACS **源码仓库**的管理，不要在 HA「设置 → 设备与服务」中删除原有 `panel_iframe` 配置条目，否则可能丢失菜单记录。
- 建议先在独立 HAOS 或完整备份恢复出的隔离测试实例演练，从 HACS 安装新仓库后重启，核实原菜单、图标和权限保留。
- 旧版的 `proxy_access` 功能已因安全风险禁用；使用它的菜单可能需要更新地址或打开模式。
- 如果遇到兼容问题，优先使用升级之前的 **HAOS 完整备份**恢复插件代码和配置。菜单管理器导出的 JSON 不能替代整机完整备份。

详细边界与恢复说明：[UPGRADE_AND_ROLLBACK.md](UPGRADE_AND_ROLLBACK.md)。

## 报告问题

[GitHub Issues](https://github.com/lenlanF/ha-sidebar-manager/issues) 反馈时请写明 HAOS/HA Core 版本、首次安装还是旧版升级、菜单模式、复现步骤和脱敏日志；不要公开 Ingress 令牌、敏感网络地址或备份文件。后续改动经测试再发布新版本。

当前 CI 覆盖 Home Assistant Core、完整 HA 前端 Chromium、WebSocket、权限、旧版格式与跨进程持久化；**实际 HACS 旧仓库切换、真实 Supervisor Ingress、HAOS 整机恢复和手机原生 App 仍待专项测试**。
