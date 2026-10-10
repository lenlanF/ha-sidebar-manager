"""Isolated validation checks: no HA runtime required.

Extract only the pure _validate function from the checked-in source via AST.
Full config flow integration is separately required before release.
"""
import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "custom_components/panel_iframe/config_flow.py"


def _validator():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_validate")
    module = ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), fn],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["_validate"]


def _form(**changes):
    return dict(title="Test", url="/config/integrations", icon="mdi:devices",
                mode="3", require_admin=False, **changes)


def test_internal_url_and_proxy_default():
    validate = _validator()
    result, errors = validate(_form())
    assert not errors
    assert result["url"] == "/config/integrations"
    assert result["proxy_access"] is False


def test_invalid_internal_uris():
    validate = _validator()
    for bad in ["https://example.com", "//evil.example", "/\\evil", ""]:
        data = _form()
        data["url"] = bad
        _, errors = validate(data)
        assert "url" in errors


def test_legacy_icon_normalization():
    validate = _validator()
    data = _form()
    data["icon"] = "mdi-robot"
    result, errors = validate(data)
    assert errors == {}
    assert result["icon"] == "mdi:robot"


def test_missing_title():
    validate = _validator()
    data = _form()
    data["title"] = "   "
    _, errors = validate(data)
    assert errors["title"] == "required"
