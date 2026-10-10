# HACS 测试预览版安装与回退指南

> **0.1.0-dev.12 · TEST PREVIEW / 测试预览版。** 仅用于自行承担风险的 HAOS 验收或隔离测试实例；不是 Home Assistant 或 HACS 官方审核/发布的稳定版，也未完成真实 HAOS/Supervisor 全量恢复及原仓库就地升级验收。

## 当前安装来源

- 自定义 HACS 仓库：`https://github.com/lenlanF/ha-sidebar-manager`
- 类别：`Integration`（集成）
- HACS 源码分支：`main`（项目默认分支）。
- 集成在磁盘上的目录：`/config/custom_components/panel_iframe/`。
- HA 集成识别域：`panel_iframe`，**不是** `ha_sidebar_manager`。
- 要求 Home Assistant **2026.10.0 或更新版本**。
- 当前仓库未创建正式 GitHub Release。按照 HACS 官方规则，无 Release 时直接使用默认分支代码；因此它在 HACS 中可能以提交短哈希而不是 `0.1.0-dev.12` 显示下载版本，集成自身版本由 `manifest.json` 提供。

## 仅在尚未安装原版 panel_iframe 时：直接通过 HACS 安装

1. 在 HAOS 中打开 **HACS → 右上角 ⋮ → 自定义存储库（Custom repositories）**。
2. 网址填写 `https://github.com/lenlanF/ha-sidebar-manager`；类型选择 **Integration**，添加。
3. 回到 HACS 搜索 **HA Sidebar Manager (Preview)**，进入仓库详情，点击下载（Download）。
4. 确认组件下载到了 `/config/custom_components/panel_iframe/`，不要创建另一个 `ha_sidebar_manager` 目录。
5. 重启 Home Assistant Core（无需整机格式化或改动 Supervisor）。
6. 打开 **设置 → 设备与服务 → 添加集成**，搜索 **HA Sidebar Manager**，选择安装侧边栏管理器。此操作建立一个 `manager_only` ConfigEntry，无需创建假菜单。
7. 用管理员帐号访问左侧「侧边栏管理」或 `/ha-sidebar-manager`，添加一个内部测试路径（例如 `/config/integrations`，模式 3）并验证可见、编辑、停用、重新启用、删除。
8. 最后重启 HA Core，确认菜单持久保存。若界面异常，检查 **设置 → 系统 → 日志** 及浏览器控制台。

## 已在 HACS 安装原版 shaonianzhentan/panel_iframe 的用户

**停在这里先做备份，切勿把两个 HACS 仓库同时设为已安装。** 两者共用 `panel_iframe` domain 和同一个安装目录，彼此更新可能覆盖对方代码，导致新旧版本混杂。**在 HA「设备与服务」中删除原版集成配置，会删除既有菜单记录；不要这样做。**

在隔离的 HAOS 或恢复出的备份副本上演练以下顺序：

1. 使用 HAOS/Supervisor **创建完整备份并复制到设备外**；另存现有 `/config/custom_components/panel_iframe/` 和原版 HACS 来源/版本信息。先记录原有菜单及 URL。
2. 在 HACS 中解除对**原作者仓库**的安装管理（相关操作可能会卸载它的代码文件），确认旧来源不会继续更新 `panel_iframe`。**仅操作 HACS 仓库/源码，不在「设置 → 设备与服务」中删除现有 `panel_iframe` 配置条目。**
3. 从 HACS 自定义仓库添加本仓库（Integration），下载测试预览代码；核实 `custom_components/panel_iframe/manifest.json` 的 `version` 为 `0.1.0-dev.12`。
4. 重启 Home Assistant Core。已有旧菜单应从原 ConfigEntry 加载，新管理器作为共享管理员菜单出现；不需要为每个旧菜单重新添加集成。
5. 在管理器中核对旧菜单的名称、图标、URL、管理员权限及开关状态；测试内部路由、允许 iframe 的页面与新窗口打开。**旧版 `proxy_access` 已因安全问题被禁用**，依赖原代理的菜单可能不再可用。
6. 如已有旧配置但看不到管理器，先检查 HA 日志、集成加载状态和是否正确下载到旧 domain 目录；不要盲目再次安装或删除原菜单配置。

**警告：** 以上升级顺序是面向 HAOS 的*待现场验证试验流程*，不是已完成的原版 HACS 仓库切换成功案例。应先在可回滚测试环境验收，再决定是否用于日常 HAOS。

## 失败恢复

- 确认完整备份是安装**之前**制作且包含 HA 配置与插件文件。优先通过 HAOS/Supervisor **恢复升级前完整备份**，一并恢复旧集成源码和旧 ConfigEntries。
- 本管理器的「导出菜单 JSON」只备份受支持菜单字段；它不能恢复 HACS 安装来源、插件代码、HA Core 全局配置或旧代理服务，不应作为唯一回滚手段。
- 如果恢复完整备份后 HACS 仍显示不一致，先核对旧来源和目录，再重启 HA Core；避免让新旧两个源同时管理同一目录。

## 测试验证与版本边界

0.1.0-dev.12 在 HA 2026.10 Core 自动化测试中通过真实 ConfigEntry/WebSocket CRUD、浏览器完整 HA 前端、桌面/窄屏 Chromium、基于原作者固定版本源码的升级/回退模拟和跨 Python 进程持久化；官方 HACS 仓库校验通过 **9/9**。参见：

- [Source checks](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38073915898)
- [HACS repository validation](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38073915985)
- [详细升级与回滚](UPGRADE_AND_ROLLBACK.md)
- [Ingress / iframe 限制](INGRESS_AND_EMBEDDING.md)

**未验证:** HACS 已安装原仓库来源实机切换、Supervisor/HAOS 整机重启/完整备份恢复、附加组件 Ingress 实际业务链路、手机 HA App 实机。HACS 结构校验通过仅说明仓库格式可识别，不证明所有 HAOS 安装场景已通过。
