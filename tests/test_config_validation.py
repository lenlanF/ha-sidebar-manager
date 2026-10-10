"""Flow validation regression tests. Requires pytest and HA test dependencies."""

from custom_components.panel_iframe.config_flow import _validate


def test_valid_internal_path():
    data, errors = _validate({
        "title": "自动化",
        "url": " /config/automation/dashboard ",
        "icon": "mdi-robot",
        "mode": "3",
        "require_admin": True,
    })
    assert not errors
    assert data["url"] == "/config/automation/dashboard"
    assert data["icon"] == "mdi:robot"
    assert data["proxy_access"] is False


def test_reject_external_url_for_internal_mode():
    _, errors = _validate({
        "title": "test",
        "url": "https://example.com",
        "icon": "mdi:link",
        "mode": "3",
    })
    assert errors["url"] == "invalid_internal_path"


def test_reject_protocol_relative_internal_url():
    _, errors = _validate({
        "title": "test",
        "url": "//example.com/redirect",
        "icon": "mdi:link",
        "mode": "3",
    })
    assert errors["url"] == "invalid_internal_path"


def test_reject_empty_title_and_url():
    _, errors = _validate({
        "title": " ",
        "url": " ",
        "icon": "mdi:link",
        "mode": "0",
    })
    assert errors["title"] == "required"
    assert errors["url"] == "required"
