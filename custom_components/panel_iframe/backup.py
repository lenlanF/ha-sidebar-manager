"""Safe, versioned backup format and preflight planning for sidebar entries.

Snapshots include effective, supported menu settings, not Home Assistant's
private .storage config-entry internals, credentials or integration metadata.
"""

from __future__ import annotations

import json
from typing import Any, Callable

BACKUP_FORMAT = "ha-sidebar-manager"
BACKUP_VERSION = 1
MAX_ITEMS = 100
MAX_BYTES = 256_000
BACKUP_FIELDS = ("title", "url", "icon", "mode", "require_admin", "enabled", "menu_order")


class BackupValidationError(ValueError):
    """The selected file cannot be restored without fixing it."""


def make_backup(items: list[dict[str, Any]], exported_at: str) -> dict[str, Any]:
    """Export a JSON-compatible snapshot without modifying HA data."""
    if len(items) > MAX_ITEMS:
        raise BackupValidationError("too_many_entries")
    result = []
    for item in items:
        record = {name: item.get(name) for name in BACKUP_FIELDS}
        record["entry_id"] = item["entry_id"]
        result.append(record)
    return {
        "format": BACKUP_FORMAT,
        "version": BACKUP_VERSION,
        "exported_at": exported_at,
        "items": result,
    }


def prepare_restore(
    backup: Any,
    existing: list[dict[str, Any]],
    validate: Callable[..., tuple[dict[str, Any], dict[str, str]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate entire file, then plan safe create/update/skip operations.

    Matching order:
    1. Same entry_id -> update settings of this integration's entry.
    2. Same title AND URL -> skip (idempotent cross-instance import).
    3. Same title but different URL -> conflict; do not overwrite by guess.
    4. No match -> create a new entry.

    The actual apply phase must run another preflight on the server; this
    planner has no writes. No delete action is ever produced.
    """
    if not isinstance(backup, dict):
        raise BackupValidationError("invalid_file")
    try:
        size = len(json.dumps(backup, ensure_ascii=False).encode("utf-8"))
    except (ValueError, TypeError, OverflowError) as exc:
        raise BackupValidationError("invalid_json") from exc
    if size > MAX_BYTES:
        raise BackupValidationError("file_too_large")
    if backup.get("format") != BACKUP_FORMAT or backup.get("version") != BACKUP_VERSION:
        raise BackupValidationError("unsupported_format_or_version")
    items = backup.get("items")
    if not isinstance(items, list) or not 0 <= len(items) <= MAX_ITEMS:
        raise BackupValidationError("invalid_item_count")

    current_by_id = {x["entry_id"]: x for x in existing}
    current_by_title = {}
    for x in existing:
        current_by_title.setdefault(x["title"].casefold(), []).append(x)

    normalized = []
    plan = []
    seen_backup_ids = set()
    targeted_ids = set()
    for index, raw in enumerate(items):
        if not isinstance(raw, dict):
            raise BackupValidationError(f"item_{index}_not_object")
        if any(key not in raw for key in BACKUP_FIELDS):
            raise BackupValidationError(f"item_{index}_missing_fields")
        eid = raw.get("entry_id", "")
        if not isinstance(eid, str) or len(eid) > 128:
            raise BackupValidationError(f"item_{index}_invalid_entry_id")
        if eid:
            if eid in seen_backup_ids:
                raise BackupValidationError(f"item_{index}_duplicate_entry_id")
            seen_backup_ids.add(eid)
        order = raw["menu_order"]
        if type(order) is not int or not 0 <= order <= 1_000_000:
            raise BackupValidationError(f"item_{index}_invalid_order")
        if not isinstance(raw["title"], str) or len(raw["title"]) > 100:
            raise BackupValidationError(f"item_{index}_invalid_title")
        if not isinstance(raw["url"], str) or len(raw["url"]) > 2048:
            raise BackupValidationError(f"item_{index}_invalid_url")
        if not isinstance(raw["icon"], str) or len(raw["icon"]) > 100:
            raise BackupValidationError(f"item_{index}_invalid_icon")
        if not isinstance(raw["mode"], str) or raw["mode"] not in ("0", "1", "2", "3"):
            raise BackupValidationError(f"item_{index}_invalid_mode")
        if type(raw["require_admin"]) is not bool or type(raw["enabled"]) is not bool:
            raise BackupValidationError(f"item_{index}_invalid_flags")

        payload = {key: raw[key] for key in BACKUP_FIELDS if key != "menu_order"}
        # Older upstream config entries may exist without any URL. A menu
        # snapshot must preserve them as unconfigured placeholders.
        values, errors = validate(payload, allow_unconfigured=True)
        if errors:
            raise BackupValidationError(f"item_{index}_validation_{','.join(errors)}")
        if values.get("title") != raw["title"].strip():
            raise BackupValidationError(f"item_{index}_invalid_title_spaces")
        values["menu_order"] = order
        title_key = values["title"].casefold()
        normalized.append(values)

        old = current_by_id.get(eid)
        if old is None:
            title_matches = current_by_title.get(title_key, [])
            exact = [x for x in title_matches if x.get("url") == values["url"]
                     and x["entry_id"] not in targeted_ids]
            if exact:
                old = exact[0]
                # A cross-instance match must restore changed icon, visibility,
                # enablement and order instead of silently skipping them.
                action = ("skip" if all(old.get(k) == values[k] for k in BACKUP_FIELDS)
                          else "update")
            elif any(x.get("url") != values["url"] for x in title_matches):
                raise BackupValidationError(f"item_{index}_title_conflict")
            else:
                # Distinct legacy entries can share the same name and URL.
                action = "create"
        else:
            action = "update"
            if all(old.get(k) == values[k] for k in BACKUP_FIELDS):
                action = "skip"

        if old and old["entry_id"] in targeted_ids:
            raise BackupValidationError(f"item_{index}_duplicate_target")
        if old:
            targeted_ids.add(old["entry_id"])
        plan.append({
            "index": index,
            "action": action,
            "entry_id": old["entry_id"] if old else None,
            "title": values["title"],
        })
    return normalized, plan
