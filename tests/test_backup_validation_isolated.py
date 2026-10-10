"""Pure restore preflight regression tests without importing Home Assistant."""

import ast
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/panel_iframe"


def _backup_module():
    spec = importlib.util.spec_from_file_location("sidebar_backup_pure", ROOT / "backup.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validator():
    path = ROOT / "config_flow.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_validate")
    mod = ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), fn],
        type_ignores=[],
    )
    ast.fix_missing_locations(mod)
    ns = {}
    exec(compile(mod, str(path), "exec"), ns)
    return ns["_validate"]


def _item(eid, title="设备", url="/config/integrations"):
    return {
        "entry_id": eid, "title": title, "url": url, "icon": "mdi:devices",
        "mode": "3", "require_admin": False, "enabled": True, "menu_order": 100000,
    }


def test_restore_preflight_is_read_only_and_can_identify_updates():
    b = _backup_module()
    snap = b.make_backup([_item("legacy")], "2026-10-10T00:00:00Z")
    existing = [_item("legacy", url="/config/logs")]
    normalized, plan = b.prepare_restore(snap, existing, _validator())
    assert normalized[0]["url"] == "/config/integrations"
    assert plan[0]["action"] == "update"
    assert existing[0]["url"] == "/config/logs"


def test_restore_same_title_different_ids_is_preserved():
    b = _backup_module()
    items = [_item("a", "同名", "/config/logs"), _item("b", "同名", "/config/integrations")]
    normalized, plan = b.prepare_restore(
        b.make_backup(items, "2026-10-10T00:00:00Z"), [], _validator()
    )
    assert len(normalized) == 2
    assert [x["action"] for x in plan] == ["create", "create"]


def test_restore_rejects_conflicts_and_dangerous_shapes():
    b = _backup_module()
    sample = b.make_backup([_item("first")], "2026-10-10T00:00:00Z")
    existing = [_item("other", "设备", "/config/logs")]
    with pytest.raises(b.BackupValidationError, match="title_conflict"):
        b.prepare_restore(sample, existing, _validator())
    for bad in (
        {**sample, "version": 99},
        {**sample, "items": [{**_item("first"), "mode": "not-valid"}]},
        {**sample, "items": [{**_item("first"), "url": "javascript:alert(1)"}]},
        {**sample, "items": [{**_item("first"), "require_admin": "false"}]},
        {**sample, "items": [{**_item("first"), "menu_order": -1}]},
        {**sample, "items": [_item("first")] * 101},
    ):
        with pytest.raises(b.BackupValidationError):
            b.prepare_restore(bad, [], _validator())


def test_empty_snapshot_is_valid_noop():
    b = _backup_module()
    snapshot = b.make_backup([], "2026-10-10T00:00:00Z")
    values, plan = b.prepare_restore(snapshot, [], _validator())
    assert values == [] and plan == []
