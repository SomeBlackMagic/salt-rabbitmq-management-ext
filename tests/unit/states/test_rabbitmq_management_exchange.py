from unittest.mock import Mock

import pytest

import saltext.rabbitmq_management.states.rabbitmq_management_exchange_mod as state


@pytest.fixture
def salt_functions():
    return {
        "rabbitmq_management.exchange_create": Mock(return_value={"status": "created"}),
        "rabbitmq_management.exchange_delete": Mock(return_value={"status": "deleted"}),
        "rabbitmq_management.exchange_exist": Mock(return_value=True),
        "rabbitmq_management.exchange_get": Mock(return_value=None),
    }


@pytest.fixture
def configure_loader_modules(salt_functions):
    return {
        state: {
            "__opts__": {"test": False},
            "__salt__": salt_functions,
        }
    }


def _exchange(type="direct", durable=True, auto_delete=False, internal=False, arguments=None):
    return {
        "name": "orders",
        "vhost": "/",
        "type": type,
        "durable": durable,
        "auto_delete": auto_delete,
        "internal": internal,
        "arguments": arguments if arguments is not None else {},
    }


def test_virtual_requires_execution_functions(salt_functions):
    assert state.__virtual__() == "rabbitmq_management"

    salt_functions.pop("rabbitmq_management.exchange_get")

    assert state.__virtual__() == (
        False,
        "Required execution functions are not available: rabbitmq_management.exchange_get",
    )


def test_exchange_present_creates_new_exchange(salt_functions):
    salt_functions["rabbitmq_management.exchange_get"].return_value = None

    ret = state.exchange_present("orders", vhost="/", type="direct", durable=True)

    assert ret == {
        "name": "orders",
        "result": True,
        "changes": {
            "old": None,
            "new": {
                "vhost": "/",
                "name": "orders",
                "type": "direct",
                "durable": True,
                "auto_delete": False,
                "internal": False,
                "arguments": {},
            },
        },
        "comment": "Exchange 'orders' created",
    }
    salt_functions["rabbitmq_management.exchange_create"].assert_called_once_with(
        "/", "orders", type="direct", durable=True, auto_delete=False, internal=False, arguments={}
    )


def test_exchange_present_no_changes_when_exchange_matches(salt_functions):
    salt_functions["rabbitmq_management.exchange_get"].return_value = _exchange()

    ret = state.exchange_present("orders", vhost="/", type="direct", durable=True)

    assert ret == {
        "name": "orders",
        "result": True,
        "changes": {},
        "comment": "Exchange 'orders' is already in the desired state",
    }
    salt_functions["rabbitmq_management.exchange_create"].assert_not_called()


def test_exchange_present_fails_on_conflicting_type_without_force(salt_functions):
    salt_functions["rabbitmq_management.exchange_get"].return_value = _exchange(type="direct")

    ret = state.exchange_present("orders", vhost="/", type="fanout", force=False)

    assert ret["result"] is False
    assert not ret["changes"]
    assert "force=True" in ret["comment"]
    salt_functions["rabbitmq_management.exchange_delete"].assert_not_called()
    salt_functions["rabbitmq_management.exchange_create"].assert_not_called()


def test_exchange_present_recreates_exchange_with_force(salt_functions):
    salt_functions["rabbitmq_management.exchange_get"].return_value = _exchange(type="direct")

    ret = state.exchange_present("orders", vhost="/", type="fanout", force=True)

    assert ret["result"] is True
    assert ret["changes"]["old"]["type"] == "direct"
    assert ret["changes"]["new"]["type"] == "fanout"
    salt_functions["rabbitmq_management.exchange_delete"].assert_called_once_with("/", "orders")
    salt_functions["rabbitmq_management.exchange_create"].assert_called_once()


def test_exchange_present_refuses_to_recreate_builtin_exchange(salt_functions):
    salt_functions["rabbitmq_management.exchange_get"].return_value = _exchange(type="direct")

    ret = state.exchange_present("amq.direct", vhost="/", type="fanout", force=True)

    assert ret["result"] is False
    assert "amq." in ret["comment"]
    salt_functions["rabbitmq_management.exchange_delete"].assert_not_called()
    salt_functions["rabbitmq_management.exchange_create"].assert_not_called()


def test_exchange_present_test_mode_create(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.exchange_get"].return_value = None

    ret = state.exchange_present("orders", vhost="/")

    assert ret == {
        "name": "orders",
        "result": None,
        "changes": {
            "old": None,
            "new": {
                "vhost": "/",
                "name": "orders",
                "type": "direct",
                "durable": True,
                "auto_delete": False,
                "internal": False,
                "arguments": {},
            },
        },
        "comment": "Exchange 'orders' would be created",
    }
    salt_functions["rabbitmq_management.exchange_create"].assert_not_called()


def test_exchange_absent_removes_exchange(salt_functions):
    salt_functions["rabbitmq_management.exchange_exist"].return_value = True

    ret = state.exchange_absent("orders", vhost="/", if_unused=False)

    assert ret == {
        "name": "orders",
        "result": True,
        "changes": {"old": "orders", "new": None},
        "comment": "Exchange 'orders' removed",
    }
    salt_functions["rabbitmq_management.exchange_delete"].assert_called_once_with(
        "/", "orders", if_unused=False
    )


def test_exchange_absent_already_absent(salt_functions):
    salt_functions["rabbitmq_management.exchange_exist"].return_value = False

    ret = state.exchange_absent("orders", vhost="/")

    assert ret == {
        "name": "orders",
        "result": True,
        "changes": {},
        "comment": "Exchange 'orders' on vhost '/' is already absent",
    }
    salt_functions["rabbitmq_management.exchange_delete"].assert_not_called()


def test_exchange_absent_refuses_to_remove_builtin_exchange(salt_functions):
    salt_functions["rabbitmq_management.exchange_exist"].return_value = True

    ret = state.exchange_absent("amq.fanout", vhost="/")

    assert ret["result"] is False
    assert "amq." in ret["comment"]
    salt_functions["rabbitmq_management.exchange_delete"].assert_not_called()


def test_exchange_absent_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.exchange_exist"].return_value = True

    ret = state.exchange_absent("orders", vhost="/")

    assert ret == {
        "name": "orders",
        "result": None,
        "changes": {"old": "orders", "new": None},
        "comment": "Exchange 'orders' would be removed",
    }
    salt_functions["rabbitmq_management.exchange_delete"].assert_not_called()
