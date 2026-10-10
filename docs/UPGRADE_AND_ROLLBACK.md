# Upgrade and recovery checklist / 升级与恢复

> **Unreleased development branch. Use a disposable Home Assistant 2026.10 test instance only. Do not replace a production HACS integration yet.**

## 1. What is backward compatible?

- This project intentionally retains the original integration domain `panel_iframe`.
- Existing menu ConfigEntries should keep their original `entry_id` and title, `data` and `options`. The new runtime combines `data` and `options` when reading settings, so old options values take precedence.
- Legacy `proxy_access` is **not** executed. The prior unrestricted proxy endpoint was removed because it lacked sufficient authorization and target restrictions.
- Extra legacy data/options keys are **not** deleted when editing an existing entry.
- The new `enabled` option defaults to `true`, so old entries do not become hidden unintentionally.
- Internal route behavior and iframe restrictions should be tested per HA version.

## 2. Required backup before changing integration files

Use Home Assistant's built-in full backup/snapshot first; save it off the HA host. Also retain a copy of the original `custom_components/panel_iframe/` directory and record the installed upstream `panel_iframe` version / HACS source. Do **not** edit `.storage/core.config_entries` by hand while HA is running.

The manager also includes **Export backup**, which downloads a versioned JSON menu snapshot to the administrator's browser. It contains only menu settings and original entry IDs, **not** a complete HA backup or any integration's hidden state. URLs may contain secrets or private hostnames; store JSON securely and never attach it to a public issue without reviewing it.

## 3. Test migration in a separate HA instance

1. Restore a copy of the *whole* HA backup into a disposable test HA.
2. Record the names, URL destinations, modes, icons, permissions, enabled states and entry IDs for existing `panel_iframe` menus.
3. After making a test copy, replace the **test** instance's `custom_components/panel_iframe` code with the development branch's integration directory, then restart the test HA.
4. Confirm every legacy item is still present and routes work; any original proxy-only URL will not be served by the new runtime.
5. Open `/ha-sidebar-manager` as an HA administrator and export a JSON menu snapshot.
6. Verify edit, disable, enable, delete only on throwaway test entries; also test a full HA restart.
7. Review browser logs, HA logs, iOS/Android screens, iframe X-Frame-Options/CSP, and add-on ingress pages.

**Never install the original and the fork simultaneously into the same `panel_iframe` directory.** HACS repository selection and upgrade paths must be tested on the disposable instance first. The code passing CI is not sufficient to guarantee a safe HACS in-place source switch.

## 4. Menu JSON backup format and restore safeguards

```json
{
  "format": "ha-sidebar-manager",
  "version": 1,
  "exported_at": "2026-10-10T00:00:00+00:00",
  "items": [{
    "entry_id": "existing-menu-id",
    "title": "设备与服务",
    "url": "/config/integrations",
    "icon": "mdi:devices",
    "mode": "3",
    "require_admin": true,
    "enabled": true,
    "menu_order": 0
  }]
}
```

Menu backup import is administrator-only, limited to 100 entries and a 256 KB payload. It **always validates the entire file before modifying anything**, and begins with a dry-run preview. Application requires a separate explicit confirmation. Existing entries are identified by ID; missing entries may be created. Exact title+URL matches from another HA instance are skipped. A title clash pointing to a different URL fails the preflight instead of silently overwriting a menu. The importer never deletes menus that are absent from the backup.

Import is **not an atomic database transaction**. A runtime failure partway through application may leave a subset of changes applied, and the result explicitly reports those completed operations. Importing the same snapshot after success is designed to be idempotent.

Imported snapshots hold the supported visible menu fields only. Unknown legacy metadata is not exported; it is **preserved** on existing entries when restoring but is not reconstructed if a menu is newly created on another HA instance. The unsafe proxy remains disabled.

## 5. Roll back the software safely

If the test instance develops a compatibility problem, **restore the full HA backup/snapshot taken in step 2**. This restores both the original integration files and HA configuration together, avoiding mismatched code and ConfigEntries. Merely importing the menu JSON is **not** a software downgrade and cannot restore old Python/JS files or deleted HA data.

Before any future production upgrade, repeat all checks with the intended HA version and establish a verified full-backup rollback route. The current repository has not been released to production.

## Additional compatibility notes (v0.1.0-dev.5)

Original `panel_iframe` versions could create a menu record with only its title. A restored title-only entry retains an empty target URL, appears as **not configured** in the manager, and has no clickable HA sidebar panel until an administrator supplies a URL. The blank URL exception is for legacy restore only, not ordinary menu creation.

When editing an old entry through the native Home Assistant options screen, unknown legacy options are preserved instead of silently discarded. The deprecated `proxy_access` feature remains deactivated for security. ConfigEntry persistence has been exercised through the HA native storage fixture, but production upgrade and an independent HA process restart still require verification on a separate installation.

## Persistence verification status (v0.1.0-dev.6)

The development CI now performs two independent Python-process passes over a native HA Core ConfigEntry storage envelope; legacy IDs and options survive a cold load. This improves confidence in storage compatibility, but **is not an in-place HACS upgrade test or a full Home Assistant restart**. Follow the complete backup and disposable-instance migration procedure above before any production installation.

## Source replacement and return-to-original rehearsal (v0.1.0-dev.7)

An isolated CI job now checks out the genuine upstream v2026.4.13 at pinned Git SHA and tests three independent Python-process stages: original ConfigFlow and native storage, fork source with old ConfigEntry cold load, and restoration of the original source plus the pre-upgrade storage snapshot. Evidence: https://github.com/lenlanF/ha-sidebar-manager/actions/runs/38057571508. The original OptionsFlow is **not** tested end to end; legacy settings are recorded through the HA native ConfigEntry API after unloading the original entry to avoid a deprecated hot-reload path.

This validates the **integration source + menu configuration compatibility boundary only**. It does not modify HACS's installed-repository metadata and is not a full Home Assistant backup or service restart. Production source migration must still be tried on a disposable full-HA installation and verified through a real HA backup/restore cycle.
