from unittest.mock import Mock

import pytest

import saltext.rabbitmq_management.states.rabbitmq_management_queue_mod as state


@pytest.fixture
def salt_functions():
    return {
        "rabbitmq_management.queue_create": Mock(return_value={"status": "created"}),
        "rabbitmq_management.queue_delete": Mock(return_value={"status": "deleted"}),
        "rabbitmq_management.queue_exist": Mock(return_value=True),
        "rabbitmq_management.queue_get": Mock(return_value=None),
    }


@pytest.fixture
def configure_loader_modules(salt_functions):
    return {
        state: {
            "__opts__": {"test": False},
            "__salt__": salt_functions,
        }
    }


def _queue(durable=True, auto_delete=False, arguments=None):
    return {
        "name": "orders",
        "vhost": "/",
        "durable": durable,
        "auto_delete": auto_delete,
        "arguments": arguments if arguments is not None else {},
        "messages": 0,
        "consumers": 0,
        "state": "running",
    }


def test_virtual_requires_execution_functions(salt_functions):
    assert state.__virtual__() == "rabbitmq_management"

    salt_functions.pop("rabbitmq_management.queue_get")

    assert state.__virtual__() == (
        False,
        "Required execution functions are not available: rabbitmq_management.queue_get",
    )


def test_queue_present_creates_new_queue(salt_functions):
    salt_functions["rabbitmq_management.queue_get"].return_value = None

    ret = state.queue_present("orders", vhost="/", durable=True, auto_delete=False)

    assert ret == {
        "name": "orders",
        "result": True,
        "changes": {
            "old": None,
            "new": {
                "vhost": "/",
                "name": "orders",
                "durable": True,
                "auto_delete": False,
                "arguments": {},
            },
        },
        "comment": "Queue 'orders' created",
    }
    salt_functions["rabbitmq_management.queue_create"].assert_called_once_with(
        "/", "orders", True, False, {}
    )


def test_queue_present_no_changes_when_queue_matches(salt_functions):
    salt_functions["rabbitmq_management.queue_get"].return_value = _queue()

    ret = state.queue_present("orders", vhost="/", durable=True, auto_delete=False, arguments=None)

    assert ret == {
        "name": "orders",
        "result": True,
        "changes": {},
        "comment": "Queue 'orders' is already in the desired state",
    }
    salt_functions["rabbitmq_management.queue_create"].assert_not_called()


def test_queue_present_fails_on_conflicting_params_without_force(salt_functions):
    salt_functions["rabbitmq_management.queue_get"].return_value = _queue(
        arguments={"x-queue-type": "classic"}
    )

    ret = state.queue_present(
        "orders",
        vhost="/",
        arguments={"x-queue-type": "quorum"},
        force=False,
    )

    assert ret["result"] is False
    assert not ret["changes"]
    assert "force=True" in ret["comment"]
    salt_functions["rabbitmq_management.queue_delete"].assert_not_called()
    salt_functions["rabbitmq_management.queue_create"].assert_not_called()


def test_queue_present_recreates_queue_with_force(salt_functions):
    salt_functions["rabbitmq_management.queue_get"].return_value = _queue(
        arguments={"x-queue-type": "classic"}
    )

    ret = state.queue_present(
        "orders",
        vhost="/",
        arguments={"x-queue-type": "quorum"},
        force=True,
    )

    assert ret["result"] is True
    assert ret["changes"]["old"]["arguments"] == {"x-queue-type": "classic"}
    assert ret["changes"]["new"]["arguments"] == {"x-queue-type": "quorum"}
    salt_functions["rabbitmq_management.queue_delete"].assert_called_once_with("/", "orders")
    salt_functions["rabbitmq_management.queue_create"].assert_called_once()


def test_queue_present_handles_json_string_arguments(salt_functions):
    salt_functions["rabbitmq_management.queue_get"].return_value = _queue(
        arguments={"x-queue-type": "quorum"}
    )

    ret = state.queue_present(
        "orders",
        vhost="/",
        arguments='{"x-queue-type": "quorum"}',
    )

    assert ret["result"] is True
    assert not ret["changes"]
    salt_functions["rabbitmq_management.queue_create"].assert_not_called()


def test_queue_present_test_mode_create(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.queue_get"].return_value = None

    ret = state.queue_present("orders", vhost="/")

    assert ret == {
        "name": "orders",
        "result": None,
        "changes": {
            "old": None,
            "new": {
                "vhost": "/",
                "name": "orders",
                "durable": True,
                "auto_delete": False,
                "arguments": {},
            },
        },
        "comment": "Queue 'orders' would be created",
    }
    salt_functions["rabbitmq_management.queue_create"].assert_not_called()


def test_queue_present_test_mode_conflict(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.queue_get"].return_value = _queue(durable=False)

    ret = state.queue_present("orders", vhost="/", durable=True, force=True)

    assert ret["result"] is None
    assert ret["changes"]["old"]["durable"] is False
    assert ret["changes"]["new"]["durable"] is True
    salt_functions["rabbitmq_management.queue_delete"].assert_not_called()
    salt_functions["rabbitmq_management.queue_create"].assert_not_called()


def test_queue_absent_removes_queue(salt_functions):
    salt_functions["rabbitmq_management.queue_exist"].return_value = True

    ret = state.queue_absent("orders", vhost="/", if_empty=False, if_unused=False)

    assert ret == {
        "name": "orders",
        "result": True,
        "changes": {"old": "orders", "new": None},
        "comment": "Queue 'orders' removed",
    }
    salt_functions["rabbitmq_management.queue_delete"].assert_called_once_with(
        "/", "orders", if_empty=False, if_unused=False
    )


def test_queue_absent_already_absent(salt_functions):
    salt_functions["rabbitmq_management.queue_exist"].return_value = False

    ret = state.queue_absent("orders", vhost="/")

    assert ret == {
        "name": "orders",
        "result": True,
        "changes": {},
        "comment": "Queue 'orders' on vhost '/' is already absent",
    }
    salt_functions["rabbitmq_management.queue_delete"].assert_not_called()


def test_queue_absent_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.queue_exist"].return_value = True

    ret = state.queue_absent("orders", vhost="/")

    assert ret == {
        "name": "orders",
        "result": None,
        "changes": {"old": "orders", "new": None},
        "comment": "Queue 'orders' would be removed",
    }
    salt_functions["rabbitmq_management.queue_delete"].assert_not_called()
