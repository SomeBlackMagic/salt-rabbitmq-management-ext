from unittest.mock import Mock

import pytest

import saltext.rabbitmq_management.states.rabbitmq_management_federation_mod as state


@pytest.fixture
def salt_functions():
    return {
        "rabbitmq_management.federation_upstream_create": Mock(return_value={"status": "created"}),
        "rabbitmq_management.federation_upstream_delete": Mock(return_value=True),
        "rabbitmq_management.federation_upstream_exist": Mock(return_value=True),
        "rabbitmq_management.federation_upstream_get": Mock(return_value=None),
    }


@pytest.fixture
def configure_loader_modules(salt_functions):
    return {
        state: {
            "__opts__": {"test": False},
            "__salt__": salt_functions,
        }
    }


def _upstream(uri="amqp://remote-server", **extra_value):
    value = {"uri": uri}
    value.update(extra_value)
    return {
        "component": "federation-upstream",
        "vhost": "/",
        "name": "my-upstream",
        "value": value,
    }


def test_virtual_requires_execution_functions(salt_functions):
    assert state.__virtual__() == "rabbitmq_management"

    salt_functions.pop("rabbitmq_management.federation_upstream_get")

    assert state.__virtual__() == (
        False,
        "Required execution functions are not available: rabbitmq_management.federation_upstream_get",
    )


def test_federation_upstream_present_creates_new_upstream(salt_functions):
    salt_functions["rabbitmq_management.federation_upstream_get"].return_value = None

    ret = state.federation_upstream_present(
        "my-upstream",
        vhost="/",
        uri="amqp://remote-server",
        prefetch_count=1000,
    )

    assert ret == {
        "name": "my-upstream",
        "result": True,
        "changes": {
            "old": None,
            "new": {
                "vhost": "/",
                "name": "my-upstream",
                "value": {"uri": "amqp://remote-server", "prefetch-count": 1000},
            },
        },
        "comment": "Federation upstream 'my-upstream' created",
    }
    salt_functions["rabbitmq_management.federation_upstream_create"].assert_called_once_with(
        "/",
        "my-upstream",
        uri="amqp://remote-server",
        expires=None,
        message_ttl=None,
        max_hops=None,
        prefetch_count=1000,
        reconnect_delay=None,
        ack_mode=None,
        trust_user_id=None,
        exchange=None,
        queue=None,
    )


def test_federation_upstream_present_no_changes_when_value_matches(salt_functions):
    salt_functions["rabbitmq_management.federation_upstream_get"].return_value = _upstream(
        uri="amqp://remote-server", **{"prefetch-count": 1000}
    )

    ret = state.federation_upstream_present(
        "my-upstream",
        vhost="/",
        uri="amqp://remote-server",
        prefetch_count=1000,
    )

    assert ret == {
        "name": "my-upstream",
        "result": True,
        "changes": {},
        "comment": "Federation upstream 'my-upstream' is already in the desired state",
    }
    salt_functions["rabbitmq_management.federation_upstream_create"].assert_not_called()


def test_federation_upstream_present_updates_changed_value(salt_functions):
    salt_functions["rabbitmq_management.federation_upstream_get"].return_value = _upstream(
        uri="amqp://remote-server", **{"prefetch-count": 500}
    )

    ret = state.federation_upstream_present(
        "my-upstream",
        vhost="/",
        uri="amqp://remote-server",
        prefetch_count=1000,
    )

    assert ret == {
        "name": "my-upstream",
        "result": True,
        "changes": {
            "old": {"value": {"uri": "amqp://remote-server", "prefetch-count": 500}},
            "new": {"value": {"uri": "amqp://remote-server", "prefetch-count": 1000}},
        },
        "comment": "Federation upstream 'my-upstream' updated",
    }
    salt_functions["rabbitmq_management.federation_upstream_create"].assert_called_once()


def test_federation_upstream_present_handles_list_uri(salt_functions):
    salt_functions["rabbitmq_management.federation_upstream_get"].return_value = None
    uris = ["amqp://node1.internal", "amqp://node2.internal"]

    ret = state.federation_upstream_present("my-upstream", vhost="/", uri=uris)

    assert ret["result"] is True
    assert ret["changes"]["new"]["value"]["uri"] == uris
    salt_functions["rabbitmq_management.federation_upstream_create"].assert_called_once_with(
        "/",
        "my-upstream",
        uri=uris,
        expires=None,
        message_ttl=None,
        max_hops=None,
        prefetch_count=None,
        reconnect_delay=None,
        ack_mode=None,
        trust_user_id=None,
        exchange=None,
        queue=None,
    )


def test_federation_upstream_present_test_mode_create(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.federation_upstream_get"].return_value = None

    ret = state.federation_upstream_present(
        "my-upstream",
        vhost="/",
        uri="amqp://remote-server",
    )

    assert ret == {
        "name": "my-upstream",
        "result": None,
        "changes": {
            "old": None,
            "new": {
                "vhost": "/",
                "name": "my-upstream",
                "value": {"uri": "amqp://remote-server"},
            },
        },
        "comment": "Federation upstream 'my-upstream' would be created",
    }
    salt_functions["rabbitmq_management.federation_upstream_create"].assert_not_called()


def test_federation_upstream_present_test_mode_update(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.federation_upstream_get"].return_value = _upstream(
        uri="amqp://old-server"
    )

    ret = state.federation_upstream_present(
        "my-upstream",
        vhost="/",
        uri="amqp://new-server",
    )

    assert ret == {
        "name": "my-upstream",
        "result": None,
        "changes": {
            "old": {"value": {"uri": "amqp://old-server"}},
            "new": {"value": {"uri": "amqp://new-server"}},
        },
        "comment": "Federation upstream 'my-upstream' would be updated",
    }
    salt_functions["rabbitmq_management.federation_upstream_create"].assert_not_called()


def test_federation_upstream_absent_removes_upstream(salt_functions):
    salt_functions["rabbitmq_management.federation_upstream_exist"].return_value = True

    ret = state.federation_upstream_absent("my-upstream", vhost="/")

    assert ret == {
        "name": "my-upstream",
        "result": True,
        "changes": {"old": "my-upstream", "new": None},
        "comment": "Federation upstream 'my-upstream' removed",
    }
    salt_functions["rabbitmq_management.federation_upstream_delete"].assert_called_once_with(
        "/", "my-upstream"
    )


def test_federation_upstream_absent_already_absent(salt_functions):
    salt_functions["rabbitmq_management.federation_upstream_exist"].return_value = False

    ret = state.federation_upstream_absent("my-upstream", vhost="/")

    assert ret == {
        "name": "my-upstream",
        "result": True,
        "changes": {},
        "comment": "Federation upstream 'my-upstream' on vhost '/' is already absent",
    }
    salt_functions["rabbitmq_management.federation_upstream_delete"].assert_not_called()


def test_federation_upstream_absent_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.federation_upstream_exist"].return_value = True

    ret = state.federation_upstream_absent("my-upstream", vhost="/")

    assert ret == {
        "name": "my-upstream",
        "result": None,
        "changes": {"old": "my-upstream", "new": None},
        "comment": "Federation upstream 'my-upstream' would be removed",
    }
    salt_functions["rabbitmq_management.federation_upstream_delete"].assert_not_called()
