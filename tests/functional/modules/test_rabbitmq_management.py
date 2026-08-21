"""Functional tests for the rabbitmq_management execution module namespace.

These tests verify that HTTP responses are correctly parsed and that all
domain-specific modules are merged into the shared ``rabbitmq_management``
virtual namespace.

The ``mock_http`` fixture (defined in ``tests/functional/conftest.py``) patches
``salt.utils.http.query`` and the private ``_get_management_config`` helper so
no real broker is required.
"""

import pytest

pytestmark = [
    pytest.mark.requires_salt_modules(
        "rabbitmq_management.test_management_api",
        "rabbitmq_management.vhost_list",
        "rabbitmq_management.user_list",
        "rabbitmq_management.queue_list",
        "rabbitmq_management.policy_list",
    ),
]

_OVERVIEW_BODY = (
    '{"rabbitmq_version": "3.12.0", "management_version": "3.12.0",'
    ' "cluster_name": "rabbit@localhost"}'
)
_VHOST_LIST_BODY = '[{"name": "/", "description": "", "tags": [], "tracing": false}]'
_USER_LIST_BODY = '[{"name": "guest", "tags": ["administrator"]}]'


def _ok(body):
    return {"status": 200, "body": body}


# ---------------------------------------------------------------------------
# test_management_api
# ---------------------------------------------------------------------------


def test_management_api_returns_connected_dict(modules, mock_http):
    mock_http.return_value = _ok(_OVERVIEW_BODY)
    result = modules.rabbitmq_management.test_management_api()
    assert isinstance(result, dict)
    assert result["connected"] is True
    assert result["rabbitmq_version"] == "3.12.0"
    assert result["cluster_name"] == "rabbit@localhost"


def test_management_api_returns_not_connected_on_error(modules, mock_http):
    mock_http.side_effect = ConnectionError("refused")
    result = modules.rabbitmq_management.test_management_api()
    assert isinstance(result, dict)
    assert result["connected"] is False
    assert "error" in result


# ---------------------------------------------------------------------------
# vhost_list
# ---------------------------------------------------------------------------


def test_vhost_list_returns_list(modules, mock_http):
    mock_http.return_value = _ok(_VHOST_LIST_BODY)
    result = modules.rabbitmq_management.vhost_list()
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["name"] == "/"


def test_vhost_list_returns_empty_list(modules, mock_http):
    mock_http.return_value = _ok("[]")
    result = modules.rabbitmq_management.vhost_list()
    assert isinstance(result, list)
    assert result == []


# ---------------------------------------------------------------------------
# user_list
# ---------------------------------------------------------------------------


def test_user_list_returns_list(modules, mock_http):
    mock_http.return_value = _ok(_USER_LIST_BODY)
    result = modules.rabbitmq_management.user_list()
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["name"] == "guest"


# ---------------------------------------------------------------------------
# queue_list
# ---------------------------------------------------------------------------


def test_queue_list_returns_list(modules, mock_http):
    mock_http.return_value = _ok("[]")
    result = modules.rabbitmq_management.queue_list()
    assert isinstance(result, list)


def test_queue_list_parses_queue_fields(modules, mock_http):
    body = '[{"name": "orders", "vhost": "/", "durable": true, "auto_delete": false}]'
    mock_http.return_value = _ok(body)
    result = modules.rabbitmq_management.queue_list()
    assert len(result) == 1
    assert result[0]["name"] == "orders"
    assert result[0]["durable"] is True
