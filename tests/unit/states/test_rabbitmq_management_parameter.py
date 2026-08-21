import json
from unittest.mock import Mock

import pytest

import saltext.rabbitmq_management.states.rabbitmq_management_parameter_mod as state


@pytest.fixture
def salt_functions():
    return {
        "rabbitmq_management.parameter_create": Mock(return_value={"status": "created"}),
        "rabbitmq_management.parameter_delete": Mock(return_value={"status": "deleted"}),
        "rabbitmq_management.parameter_exist": Mock(return_value=True),
        "rabbitmq_management.parameter_get": Mock(return_value=None),
    }


@pytest.fixture
def configure_loader_modules(salt_functions):
    return {
        state: {
            "__opts__": {"test": False},
            "__salt__": salt_functions,
        }
    }


def _parameter(value, component="federation-upstream", vhost="/", name="my-param"):
    return {
        "component": component,
        "vhost": vhost,
        "name": name,
        "value": value,
    }


def test_virtual_requires_execution_functions(salt_functions):
    assert state.__virtual__() == "rabbitmq_management"

    salt_functions.pop("rabbitmq_management.parameter_get")

    assert state.__virtual__() == (
        False,
        "Required execution functions are not available: rabbitmq_management.parameter_get",
    )


def test_parameter_present_creates_new_parameter(salt_functions):
    salt_functions["rabbitmq_management.parameter_get"].return_value = None
    desired_value = {"uri": "amqp://server", "expires": 3600000}

    ret = state.parameter_present(
        "my-param",
        component="federation-upstream",
        vhost="/",
        value=desired_value,
    )

    assert ret == {
        "name": "my-param",
        "result": True,
        "changes": {
            "old": None,
            "new": {
                "component": "federation-upstream",
                "vhost": "/",
                "name": "my-param",
                "value": desired_value,
            },
        },
        "comment": "Parameter 'my-param' (component: federation-upstream) created",
    }
    salt_functions["rabbitmq_management.parameter_create"].assert_called_once_with(
        "federation-upstream", "/", "my-param", desired_value
    )


def test_parameter_present_no_changes_when_value_matches(salt_functions):
    desired_value = {"uri": "amqp://server", "expires": 3600000}
    salt_functions["rabbitmq_management.parameter_get"].return_value = _parameter(desired_value)

    ret = state.parameter_present(
        "my-param",
        component="federation-upstream",
        vhost="/",
        value=desired_value,
    )

    assert ret == {
        "name": "my-param",
        "result": True,
        "changes": {},
        "comment": "Parameter 'my-param' (component: federation-upstream) is already in the desired state",
    }
    salt_functions["rabbitmq_management.parameter_create"].assert_not_called()


def test_parameter_present_updates_changed_value(salt_functions):
    old_value = {"uri": "amqp://old-server"}
    new_value = {"uri": "amqp://new-server", "expires": 3600000}
    salt_functions["rabbitmq_management.parameter_get"].return_value = _parameter(old_value)

    ret = state.parameter_present(
        "my-param",
        component="federation-upstream",
        vhost="/",
        value=new_value,
    )

    assert ret == {
        "name": "my-param",
        "result": True,
        "changes": {
            "old": {"value": old_value},
            "new": {"value": new_value},
        },
        "comment": "Parameter 'my-param' (component: federation-upstream) updated",
    }
    salt_functions["rabbitmq_management.parameter_create"].assert_called_once_with(
        "federation-upstream", "/", "my-param", new_value
    )


def test_parameter_present_handles_json_string_value(salt_functions):
    salt_functions["rabbitmq_management.parameter_get"].return_value = None
    desired_value = {"uri": "amqp://server", "expires": 3600000}

    ret = state.parameter_present(
        "my-param",
        component="federation-upstream",
        vhost="/",
        value=json.dumps(desired_value),
    )

    assert ret["result"] is True
    assert ret["changes"]["new"]["value"] == desired_value
    salt_functions["rabbitmq_management.parameter_create"].assert_called_once_with(
        "federation-upstream", "/", "my-param", desired_value
    )


def test_parameter_present_test_mode_create(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.parameter_get"].return_value = None
    desired_value = {"uri": "amqp://server"}

    ret = state.parameter_present(
        "my-param",
        component="federation-upstream",
        vhost="/",
        value=desired_value,
    )

    assert ret == {
        "name": "my-param",
        "result": None,
        "changes": {
            "old": None,
            "new": {
                "component": "federation-upstream",
                "vhost": "/",
                "name": "my-param",
                "value": desired_value,
            },
        },
        "comment": "Parameter 'my-param' (component: federation-upstream) would be created",
    }
    salt_functions["rabbitmq_management.parameter_create"].assert_not_called()


def test_parameter_present_test_mode_update(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    old_value = {"uri": "amqp://old-server"}
    new_value = {"uri": "amqp://new-server"}
    salt_functions["rabbitmq_management.parameter_get"].return_value = _parameter(old_value)

    ret = state.parameter_present(
        "my-param",
        component="federation-upstream",
        vhost="/",
        value=new_value,
    )

    assert ret == {
        "name": "my-param",
        "result": None,
        "changes": {
            "old": {"value": old_value},
            "new": {"value": new_value},
        },
        "comment": "Parameter 'my-param' (component: federation-upstream) would be updated",
    }
    salt_functions["rabbitmq_management.parameter_create"].assert_not_called()


def test_parameter_absent_removes_parameter(salt_functions):
    salt_functions["rabbitmq_management.parameter_exist"].return_value = True

    ret = state.parameter_absent("my-param", component="federation-upstream", vhost="/")

    assert ret == {
        "name": "my-param",
        "result": True,
        "changes": {"old": "my-param", "new": None},
        "comment": "Parameter 'my-param' (component: federation-upstream) removed",
    }
    salt_functions["rabbitmq_management.parameter_delete"].assert_called_once_with(
        "federation-upstream", "/", "my-param"
    )


def test_parameter_absent_already_absent(salt_functions):
    salt_functions["rabbitmq_management.parameter_exist"].return_value = False

    ret = state.parameter_absent("my-param", component="federation-upstream", vhost="/")

    assert ret == {
        "name": "my-param",
        "result": True,
        "changes": {},
        "comment": "Parameter 'my-param' (component: federation-upstream) on vhost '/' is already absent",
    }
    salt_functions["rabbitmq_management.parameter_delete"].assert_not_called()


def test_parameter_absent_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.parameter_exist"].return_value = True

    ret = state.parameter_absent("my-param", component="federation-upstream", vhost="/")

    assert ret == {
        "name": "my-param",
        "result": None,
        "changes": {"old": "my-param", "new": None},
        "comment": "Parameter 'my-param' (component: federation-upstream) would be removed",
    }
    salt_functions["rabbitmq_management.parameter_delete"].assert_not_called()
