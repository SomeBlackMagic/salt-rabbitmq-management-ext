"""Integration tests for the rabbitmq_management execution module.

These tests require a live RabbitMQ instance.  In CI the broker is started by
the project's ``compose.yaml``.  Run with::

    nox -e tests-3 -- -m integration tests/integration/

Mark: ``integration``
"""

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_salt_modules(
        "rabbitmq_management.test_management_api",
        "rabbitmq_management.vhost_list",
        "rabbitmq_management.vhost_create",
        "rabbitmq_management.vhost_exist",
        "rabbitmq_management.vhost_delete",
        "rabbitmq_management.user_list",
        "rabbitmq_management.user_create",
        "rabbitmq_management.user_exist",
        "rabbitmq_management.user_delete",
    ),
]

_VHOST = "/integration-test"
_USER = "integration-test-user"


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------


def test_management_api_is_reachable(salt_call_cli, rabbitmq_service):
    """Management API responds and reports connected=True."""
    ret = salt_call_cli.run(
        "rabbitmq_management.test_management_api",
        **rabbitmq_service,
    )
    assert ret.returncode == 0
    assert ret.data["connected"] is True


# ---------------------------------------------------------------------------
# vhost lifecycle
# ---------------------------------------------------------------------------


def test_vhost_create_and_delete(salt_call_cli, rabbitmq_service):
    """Create, verify, and delete a virtual host through the execution module."""
    # Create
    ret = salt_call_cli.run(
        "rabbitmq_management.vhost_create",
        _VHOST,
        **rabbitmq_service,
    )
    assert ret.returncode == 0

    # Verify exists
    ret = salt_call_cli.run(
        "rabbitmq_management.vhost_exist",
        _VHOST,
        **rabbitmq_service,
    )
    assert ret.returncode == 0
    assert ret.data is True

    # Delete
    ret = salt_call_cli.run(
        "rabbitmq_management.vhost_delete",
        _VHOST,
        **rabbitmq_service,
    )
    assert ret.returncode == 0

    # Verify absent
    ret = salt_call_cli.run(
        "rabbitmq_management.vhost_exist",
        _VHOST,
        **rabbitmq_service,
    )
    assert ret.returncode == 0
    assert ret.data is False


def test_vhost_list_includes_default_vhost(salt_call_cli, rabbitmq_service):
    """vhost_list returns at least the default ``/`` virtual host."""
    ret = salt_call_cli.run("rabbitmq_management.vhost_list", **rabbitmq_service)
    assert ret.returncode == 0
    assert isinstance(ret.data, list)
    names = [v["name"] for v in ret.data]
    assert "/" in names


# ---------------------------------------------------------------------------
# user lifecycle
# ---------------------------------------------------------------------------


def test_user_create_and_delete(salt_call_cli, rabbitmq_service):
    """Create, verify, and delete a user through the execution module."""
    # Create
    conn = {k: v for k, v in rabbitmq_service.items() if k != "password"}
    ret = salt_call_cli.run(
        "rabbitmq_management.user_create",
        _USER,
        password="s3cr3t",
        tags="monitoring",
        **conn,
    )
    assert ret.returncode == 0

    # Verify exists
    ret = salt_call_cli.run(
        "rabbitmq_management.user_exist",
        _USER,
        **rabbitmq_service,
    )
    assert ret.returncode == 0
    assert ret.data is True

    # Delete
    ret = salt_call_cli.run(
        "rabbitmq_management.user_delete",
        _USER,
        **rabbitmq_service,
    )
    assert ret.returncode == 0

    # Verify absent
    ret = salt_call_cli.run(
        "rabbitmq_management.user_exist",
        _USER,
        **rabbitmq_service,
    )
    assert ret.returncode == 0
    assert ret.data is False


def test_user_list_includes_guest(salt_call_cli, rabbitmq_service):
    """user_list returns at least the built-in ``guest`` user."""
    ret = salt_call_cli.run("rabbitmq_management.user_list", **rabbitmq_service)
    assert ret.returncode == 0
    assert isinstance(ret.data, list)
    names = [u["name"] for u in ret.data]
    assert "guest" in names
