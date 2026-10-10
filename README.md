# HA Sidebar Manager / Home Assistant 侧边栏管理器

[中文](README.md)

> Work in progress / 开发中。**当前仓库尚无可安装的 HACS 发布版本。**

A visual Home Assistant sidebar manager based on [shaonianzhentan/panel_iframe](https://github.com/shaonianzhentan/panel_iframe).

## Goals / 开发目标

- Manage sidebar entries in a visual UI: add, edit, remove, enable, order and group.
- Open HA internal routes, integration pages and add-on panels without wrapping HA inside an iframe.
- Support external webpages (iframe where allowed, or opening a new tab).
- Configure icon, display name, supported access modes and user visibility.
- Preserve existing `panel_iframe` config entries and migrate safely.
- Keep Home Assistant core untouched; support installation through HACS.
- Validate access on the backend, rather than treating hidden sidebar items as authorization.

## Roadmap

1. **Compatibility foundation**: import original source with license notices, fix configuration flow and panel registration/lifecycle, add tests.
2. **Management UI**: unified panel, drag-and-drop ordering, visual forms and clear status/errors.
3. **Advanced features**: permissions, backup/import/export, responsive design, compatibility matrix and release checks.

## Compatibility

The initial implementation will retain the original integration domain `panel_iframe` for migration compatibility. It will not be renamed to `ha_sidebar_manager` until safe migration is designed and tested.

## Development status

See [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) and [CHANGELOG.md](CHANGELOG.md). No runtime compatibility claims are made until HA integration tests are recorded.

## Credits and license

Based on the MIT-licensed project by [shaonianzhentan](https://github.com/shaonianzhentan/panel_iframe). Preserve the original copyright notice when copying or adapting source files.

## Security

Never expose privileged HA routes or backend operations merely by toggling sidebar visibility. Avoid exposing arbitrary HTTP proxy targets without strict security design and explicit safeguards.
