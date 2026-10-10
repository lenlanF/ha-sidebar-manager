"""Isolated backend WebSocket logic tests using fake Home Assistant objects.

This verifies the core CRUD decisions without pretending to test a running HA
instance. The tests parse functions from checked-in Python and remove their
framework decorators; decorator presence is checked separately.
"""

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1] / "custom_components/panel_iframe"


def load_functions(path, names, namespace):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    funcs = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            node.decorator_list = []
            funcs.append(node)
    assert len(funcs) == len(names)
    module = ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *funcs],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    exec(compile(module, str(ROOT / path), "exec"), namespace)
    return namespace


class Entry:
    def __init__(self, eid, title="菜单", data=None, options=None, domain="panel_iframe"):
        self.entry_id, self.title, self.domain = eid, title, domain
        self.data = data or {}
        self.options = options or {}


class Entries:
    def __init__(self, items):
        self.items = items
        self.reloaded = []
        self.deleted = []
        self.created = []
        self.flow = SimpleNamespace(async_init=self.flow_init)

    def async_entries(self, domain):
        return [entry for entry in self.items if entry.domain == domain]

    def async_get_entry(self, eid):
        return next((entry for entry in self.items if entry.entry_id == eid), None)

    def async_update_entry(self, entry, **kwargs):
        for k, v in kwargs.items():
            setattr(entry, k, v)

    async def async_reload(self, eid):
        self.reloaded.append(eid)
        return True

    async def async_remove(self, eid):
        self.deleted.append(eid)
        self.items = [entry for entry in self.items if entry.entry_id != eid]
        return True

    async def flow_init(self, domain, context, data):
        assert domain == "panel_iframe" and context["source"] == "user"
        self.created.append(data)
        self.items.append(Entry("created", title=data["title"], data=data))
        return {"type": "create_entry"}


class Conn:
    def __init__(self):
        self.result = None
        self.error = None

    def send_result(self, msgid, value=None):
        self.result = value

    def send_error(self, msgid, code, detail):
        self.error = (code, detail)


def manager():
    ns = {
        "DOMAIN": "panel_iframe",
        "SOURCE_USER": "user",
        "websocket_api": SimpleNamespace(ERR_NOT_FOUND="not_found", ERR_INVALID_FORMAT="invalid_format"),
    }
    load_functions("config_flow.py", ["_validate"], ns)
    load_functions("manager_api.py", ["_entries", "_item", "ws_list", "ws_save", "ws_delete", "ws_reorder"], ns)
    return ns


def sample():
    return {"title": "设备与服务", "url": "/config/integrations", "icon": "mdi:devices",
            "mode": "3", "require_admin": True}


def test_ws_commands_all_require_admin():
    tree = ast.parse((ROOT / "manager_api.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("ws_"):
            assert any(
                isinstance(d, ast.Attribute) and d.attr == "require_admin"
                for d in node.decorator_list
            ), node.name


def test_listing_reads_legacy_data_and_options():
    ns = manager()
    entries = Entries([
        Entry("old", "旧菜单", {"title": "旧菜单"},
              {"url": "/config/logs", "mode": "3"}),
        Entry("new", "新菜单", {"url": "https://example.org", "icon": "mdi:web"},
              {"menu_order": 0}),
        Entry("other", domain="other"),
    ])
    conn = Conn()
    ns["ws_list"](SimpleNamespace(config_entries=entries), conn, {"id": 1})
    assert [x["entry_id"] for x in conn.result] == ["new", "old"]
    assert conn.result[1]["url"] == "/config/logs"


def test_creating_uses_native_config_flow():
    ns = manager()
    entries = Entries([])
    conn = Conn()
    asyncio.run(ns["ws_save"](SimpleNamespace(config_entries=entries),
                              conn, {"id": 1, **sample()}))
    assert conn.result == {"created": True}
    assert entries.created[0]["proxy_access"] is False


def test_modification_preserves_old_options():
    ns = manager()
    entry = Entry("old", "旧标题", {"url": "/old"}, {"menu_order": 3, "proxy_access": True})
    entries = Entries([entry])
    conn = Conn()
    asyncio.run(ns["ws_save"](SimpleNamespace(config_entries=entries),
                              conn, {"id": 1, "entry_id": "old", **sample()}))
    assert conn.result == {"entry_id": "old"}
    assert entry.title == "设备与服务"
    assert entry.options["menu_order"] == 3
    assert entry.options["proxy_access"] is False
    assert entry.options["url"] == "/config/integrations"


def test_cannot_delete_unrelated_entry():
    ns = manager()
    entries = Entries([Entry("foreign", domain="another")])
    conn = Conn()
    asyncio.run(ns["ws_delete"](SimpleNamespace(config_entries=entries),
                                conn, {"id": 1, "entry_id": "foreign"}))
    assert conn.error[0] == "not_found"
    assert entries.deleted == []


def test_delete_own_entry():
    ns = manager()
    entries = Entries([Entry("old")])
    conn = Conn()
    asyncio.run(ns["ws_delete"](SimpleNamespace(config_entries=entries),
                                conn, {"id": 1, "entry_id": "old"}))
    assert conn.result == {"deleted": True}
    assert entries.deleted == ["old"]


def test_reorder_rejects_partial_and_duplicates():
    ns = manager()
    entries = Entries([Entry("a"), Entry("b")])
    for ids in (["a"], ["a", "a"], ["a", "foreign"]):
        conn = Conn()
        asyncio.run(ns["ws_reorder"](SimpleNamespace(config_entries=entries),
                                    conn, {"id": 1, "entry_ids": ids}))
        assert conn.error[0] == "invalid_format"
    assert entries.items[0].options == {}


def test_reorder_persists_manager_order():
    ns = manager()
    entries = Entries([Entry("a"), Entry("b")])
    conn = Conn()
    asyncio.run(ns["ws_reorder"](SimpleNamespace(config_entries=entries),
                                conn, {"id": 1, "entry_ids": ["b", "a"]}))
    assert conn.result == {"saved": True}
    assert entries.items[1].options["menu_order"] == 0
    assert entries.items[0].options["menu_order"] == 1


def test_manager_bootstrap_entry_is_not_a_menu():
    ns = manager()
    entries = Entries([
        Entry("manager", "HA Sidebar Manager", {"manager_only": True}),
        Entry("legacy", "旧菜单", {"url": "/config/integrations"}),
    ])
    hass = SimpleNamespace(config_entries=entries)
    conn = Conn()
    ns["ws_list"](hass, conn, {"id": 1})
    assert [x["entry_id"] for x in conn.result] == ["legacy"]
    conn = Conn()
    asyncio.run(ns["ws_delete"](hass, conn, {"id": 2, "entry_id": "manager"}))
    assert conn.error[0] == "not_found"
    assert entries.deleted == []
