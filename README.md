# HA Sidebar Manager / Home Assistant 侧边栏管理器

> **Development preview only / 开发预览：尚未发布 HACS 正式安装版本。** 请勿直接替换生产 HA 中的旧插件。

在 [shaonianzhentan/panel_iframe](https://github.com/shaonianzhentan/panel_iframe)（MIT）基础上升级的 Home Assistant 可视化侧边栏管理集成。

## 当前开发功能（dev/compat-foundation）

- 管理员专属侧边栏面板：`/ha-sidebar-manager`。
- 可视化创建、编辑和删除菜单；管理旧版 `panel_iframe` 的配置记录。
- 内置页面（HA 路由）、iframe 嵌入、全屏 iframe、新窗口链接四种模式。
- 菜单搜索、MDI 图标、管理员可见设置、管理列表上下排序。
- 采用 Home Assistant ConfigEntry 原生存储，后端 WebSocket 命令通过 `require_admin` 控制权限。
- 向后兼容原 `panel_iframe` domain；旧 `data` 与 `options` 合并读取。
- 安装时可选择「安装侧边栏管理器」，无需先创建一个无意义的菜单。
- 禁用未经授权的旧代理功能，不执行旧 `proxy_access` 参数。

## 已知限制

- **已在独立 HA 2026.10 Core 测试实例中完成 7 项集成测试，包括真实 WebSocket CRUD 和非管理员权限；并通过模拟 HA 连接的 Chromium 桌面/手机 UI 测试。尚未在实际运行的 HA 浏览器和生产设备上验收。**
- 当前上下排序只控制管理列表，HA 左侧菜单排序可能被用户自身的设置覆盖。
- 尚无菜单分组、拖拽排序、按指定用户显示、备份导入导出和自动识别所有集成。
- 旧的 MDI 图标预览静态资源未完整迁移，但新的管理界面不再依赖这些资源。
- 目标网页如果禁止 iframe 嵌入，需改成新窗口模式；HTTPS 页面无法普遍嵌入 HTTP 站点。
- 旧 HTTP 代理入口因缺少安全边界而停用。

## 开发环境下的安装流程（待实际验证）

1. **先备份** `/config` 文件夹和 `.storage/core.config_entries`，不要手动编辑 `.storage`。
2. 准备一套**独立测试用** Home Assistant 环境，不要在正式 HA 上直接覆盖旧插件。
3. 在测试 HA 的 `/config/custom_components/panel_iframe/` 放入本项目对应目录，并重启 HA。
4. 在「设置 → 设备与服务 → 添加集成」中搜索 `HA Sidebar Manager`，选择「安装侧边栏管理器」。
5. 在左侧打开「侧边栏管理」，验证新增、编辑、删除、路径打开以及重启后配置保留。
6. 有现有旧配置时，先备份，再在测试环境验证旧菜单迁移和操作一致性。

安装方法仍是开发说明，**不是经过测试的正式安装指南**。正式发布前必须验证安全升级路径，避免与旧 HACS 仓库相互覆盖。

## 开发与测试

- `python -m pytest -q tests/test_validation_isolated.py tests/test_manager_isolated.py`
- GitHub Actions：Python 语法、JSON、JavaScript、隔离 CRUD 测试和 Home Assistant Core API 导入烟雾测试。
- 验收门槛：完整安装、多菜单重载、真实浏览器 WebSocket CRUD、旧配置兼容、权限、回滚和移动端。

详见 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)、[CHANGELOG.md](CHANGELOG.md) 与 [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)。

## License

MIT. 原项目版权归 shaonianzhentan 所有，并保留在 [LICENSE](LICENSE) 中。

## 验证记录（2026-10-10）

- HA Core 配置与 WebSocket 功能测试：**7/7 通过** — [GitHub Actions](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38041795993)。
- HACS 官方仓库结构校验：**9/9 全部通过**，包括 Topics 与品牌资源 — [HACS 校验](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38041489760)。
- 已验证仓库设置 Topics：`home-assistant`、`homeassistant`、`hacs`、`sidebar`、`smart-home`。
- 上述测试不是 HA 前端浏览器、Android/iOS 或原插件生产升级的验收证据；正式 HACS 版本仍未发布。

## 开发版进展：v0.1.0-dev.2

- 可视化管理器增加菜单 **启用/停用**，不会删除原有配置；旧菜单默认启用。
- 修复最后一条菜单卸载后的共享管理器残留，以及再次加载时重复注册 WebSocket 命令的风险。
- 自动化 HA 2026.10 Core 功能测试已扩展到 **7/7 通过**；另外新增了 DOM 模拟交互检查。
- 验证：[GitHub Actions](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38041489728)。
- 已通过模拟 HA WebSocket 的 Chromium 桌面/手机 UI 测试。仍需真实 HA 中的浏览器、Ingress 和从原插件安装升级测试；尚不属于可交付的 HACS 发布版。

## 浏览器界面验证

- 使用 Chromium 在 **1366×768（桌面）** 与 **375×812（手机）** 下进行菜单增删改、启停、布局边界检查，**2/2 通过**。[运行记录](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38041795993)
- 浏览器测试的后端 WebSocket 为模拟实现；HA Core 功能测试则使用独立 HA 2026.10 实例。两种测试互补，但尚未覆盖完整 HA 前端与真实服务器之间的交互。

## 菜单备份、导入预览与恢复（v0.1.0-dev.3）

开发分支的「侧边栏管理」页面新增 **导出备份 / 导入备份** 按钮。菜单快照在管理员浏览器下载为 JSON 文件；导入会先由后端完成全量校验并显示“新增、恢复已有、跳过”的预览，只有再次确认才修改数据。

- 保留旧 `panel_iframe` 菜单的 ID、标题、URL、图标、打开模式、启停状态和管理列表顺序；仍通过 HA 原生 ConfigEntry 存储。
- 恢复优先按已有菜单 ID 匹配；跨实例导入时根据菜单名称与路径识别已有项；同名但不同路径的独立旧菜单不会合并。
- 导入**不会自动删除其他菜单**，重复导入可跳过相同项目；遇到冲突先报错，不静默覆盖。
- 单次上限 100 个菜单、256 KB；仅 HA 管理员可操作。文件中的 URL 可能含私密内网地址或访问凭据，请妥善保存。
- **菜单 JSON 不是 Home Assistant 完整备份，也不能保证事务性回滚**。恢复过程中若运行时失败，可能部分操作成功，界面会提示核对。真正的插件降级必须使用事先保存的 HA 完整备份。

详细测试/升级/回退操作见 [docs/UPGRADE_AND_ROLLBACK.md](docs/UPGRADE_AND_ROLLBACK.md)。

**最新验证**：HA 2026.10 Core 功能测试 **12/12 通过**，Chromium 桌面/手机交互、源码及 API 导入均通过 — [Source checks](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38043711432)；HACS 官方校验 **9/9 通过** — [HACS](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38043711445)。上述浏览器测试使用模拟 WebSocket，不能替代在真实 HA 前端中的手动验收，尚未发布正式版本。

## 升级兼容进度：v0.1.0-dev.4

- 已按原版 `shaonianzhentan/panel_iframe` 2026.4.13 的实际 `data.title` + `options` 配置结构建立**脱敏模拟样本**，并测试菜单在新集成中加载、管理和通过 HA 选项页面继续修改。
- 修复跨实例恢复时“名称、URL 相同但图标/权限/启停/排序不同被跳过”的问题。
- 新增 HA HTTP 测试，确认两个前端 JS 文件可通过真实 HA 资源路由读取。
- 自动化验证：[HA 2026.10 Core 16/16 + Chromium 桌面/手机](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38050016651)。
- **仍未**实际在 HACS 已安装旧版插件的 HA 实例中执行覆盖升级、重启和全备份回退；不能将上述自动化测试视作生产升级验收。

## 开发版 v0.1.0-dev.5：旧配置保存完整性

- 原版菜单从 HA 原生选项页编辑时，不再清空新版本尚未识别的历史配置字段；旧的危险代理选项仍保持关闭。
- 支持备份并恢复原版“只有菜单名称、尚未填写 URL”的记录，不强迫删除这类半配置菜单；正常新增入口仍要求填写 URL。
- 使用 HA 原生存储测试验证配置可序列化保存，包括菜单 ID、名称、旧字段和新设置。这**不等于**已完成 HA 整机重启、生产迁移或完整回滚验证。
- 自动化结果：[HA Core 19/19、Chromium 桌面/手机](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38053139374)；[HACS 9/9](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38053139396)。
- 仍为未发布开发分支；旧插件实际 HACS 原地升级请先按升级与回滚文档在独立 HA 中验证。

## 开发版 v0.1.0-dev.6：跨进程配置恢复验证

- 新增独立 CI 任务：两个**独立 Python 进程**分别执行 HA Core 原生配置保存，以及从磁盘 JSON 快照创建新配置管理器并加载原有菜单。
- 已验证旧菜单 ID、名称、URL、未知历史字段、未配置菜单、启用/停用状态在这种冷加载测试中保持正确。
- 最新证据：[跨进程及 HA Core 测试](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38054007697)（保存进程和读取进程各 1 项通过；19 项常规 HA Core 功能测试通过），[HACS 官方 9/9 校验](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38054007745)。
- **重要边界**：测试使用独立 Python 进程和 HA Core Store 加载器，但未启动两次完整 HA 服务，也未在 HACS 中原地替换已安装的原插件。正式安装与整机备份回退仍须在隔离 HA 实例中验证。

## 开发版 v0.1.0-dev.7：原版源码升级与回退演练

本轮不再只用模拟旧菜单。GitHub Actions 会从原作者仓库检出 **2026.4.13 固定提交**，用原版 ConfigFlow 建立菜单，经过 HA 原生配置存储后在另一 Python 进程切换到本项目源码加载；随后再切回原版源码和升级前配置快照，验证原菜单能够恢复。

- **三阶段分别通过**：原版创建/保存 → 新版读取并显示 → 原版源码及配置恢复。
- 保存菜单的 URL 等旧版 OptionsFlow 字段时使用 HA 原生 ConfigEntry API，避开原版已过时的热重载逻辑；**未模拟原版 OptionsFlow UI 成功**。
- 相关测试与常规 19 项 HA Core 功能测试、Chromium 桌面/手机检查全部通过：[完整 CI](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38057571508)；[HACS 校验](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38057571332)。
- **尚不等于实际 HACS 仓库来源切换、HA 完整进程重启或 Supervisor 完整备份回退**。继续限制在开发分支，不能据此建议直接覆盖生产插件。
