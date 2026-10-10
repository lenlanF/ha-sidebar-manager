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

- **已在独立 HA 2026.10 Core 测试实例中完成 5 项集成测试（包括真实 WebSocket CRUD 和只读用户拒绝访问），但尚未进行真实浏览器与生产设备验收。**
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

- HA Core 配置与 WebSocket 功能测试：**5/5 通过** — [GitHub Actions](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38040925266)。
- HACS 官方结构校验：**8/9 通过**，品牌图标已符合要求，唯一剩余项是仓库 Topics — [HACS 校验](https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38040715657)。
- 仓库所有者可在 GitHub About 中设置 Topics：`home-assistant`、`homeassistant`、`hacs`、`sidebar`、`smart-home`。
- 上述测试不是 HA 前端浏览器、Android/iOS 或原插件生产升级的验收证据；正式 HACS 版本仍未发布。
