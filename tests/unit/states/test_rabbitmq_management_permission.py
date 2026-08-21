from unittest.mock import Mock

import pytest

import saltext.rabbitmq_management.states.rabbitmq_management_permission_mod as state


@pytest.fixture
def salt_functions(monkeypatch):
    functions = {
        "rabbitmq_management.permission_set": Mock(return_value={"status": "set"}),
        "rabbitmq_management.permission_delete": Mock(return_value={"status": "deleted"}),
        "rabbitmq_management.permission_exist": Mock(return_value=False),
        "rabbitmq_management.permission_get": Mock(return_value=None),
    }
    monkeypatch.setattr(state, "__salt__", functions, raising=False)
    monkeypatch.setattr(state, "__opts__", {"test": False}, raising=False)
    return functions


def test_virtual_requires_execution_functions(salt_functions):
    assert state.__virtual__() == "rabbitmq_management"

    salt_functions.pop("rabbitmq_management.permission_get")

    assert state.__virtual__() == (
        False,
        "Required execution functions are not available: rabbitmq_management.permission_get",
    )


def test_permission_present_sets_permissions_for_new_user(salt_functions):
    ret = state.permission_present("/", "myuser", configure=".*", write=".*", read=".*")

    assert ret == {
        "name": "/",
        "result": True,
        "changes": {
            "old": None,
            "new": {"vhost": "/", "user": "myuser", "configure": ".*", "write": ".*", "read": ".*"},
        },
        "comment": "Permission for user 'myuser' on vhost '/' set",
    }
    salt_functions["rabbitmq_management.permission_set"].assert_called_once_with(
        vhost="/", user="myuser", configure=".*", write=".*", read=".*"
    )


def test_permission_present_no_changes_when_permissions_match(salt_functions):
    salt_functions["rabbitmq_management.permission_get"].return_value = {
        "user": "myuser",
        "vhost": "/",
        "configure": ".*",
        "write": ".*",
        "read": ".*",
    }

    ret = state.permission_present("/", "myuser", configure=".*", write=".*", read=".*")

    assert ret == {
        "name": "/",
        "result": True,
        "changes": {},
        "comment": "Permission for user 'myuser' on vhost '/' is already in the desired state",
    }
    salt_functions["rabbitmq_management.permission_set"].assert_not_called()


def test_permission_present_updates_changed_permissions(salt_functions):
    salt_functions["rabbitmq_management.permission_get"].return_value = {
        "user": "myuser",
        "vhost": "/",
        "configure": ".*",
        "write": ".*",
        "read": ".*",
    }

    ret = state.permission_present("/", "myuser", configure="^myapp-.*", write=".*", read=".*")

    assert ret == {
        "name": "/",
        "result": True,
        "changes": {
            "old": {"configure": ".*"},
            "new": {"configure": "^myapp-.*"},
        },
        "comment": "Permission for user 'myuser' on vhost '/' updated",
    }
    salt_functions["rabbitmq_management.permission_set"].assert_called_once_with(
        vhost="/", user="myuser", configure="^myapp-.*", write=".*", read=".*"
    )


def test_permission_present_test_mode_create(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True}, raising=False)

    ret = state.permission_present("/", "myuser")

    assert ret == {
        "name": "/",
        "result": None,
        "changes": {
            "old": None,
            "new": {"vhost": "/", "user": "myuser", "configure": ".*", "write": ".*", "read": ".*"},
        },
        "comment": "Permission for user 'myuser' on vhost '/' would be set",
    }
    salt_functions["rabbitmq_management.permission_set"].assert_not_called()


def test_permission_present_test_mode_update(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True}, raising=False)
    salt_functions["rabbitmq_management.permission_get"].return_value = {
        "user": "myuser",
        "vhost": "/",
        "configure": ".*",
        "write": ".*",
        "read": "^myapp-.*",
    }

    ret = state.permission_present("/", "myuser", configure=".*", write=".*", read=".*")

    assert ret == {
        "name": "/",
        "result": None,
        "changes": {
            "old": {"read": "^myapp-.*"},
            "new": {"read": ".*"},
        },
        "comment": "Permission for user 'myuser' on vhost '/' would be updated",
    }
    salt_functions["rabbitmq_management.permission_set"].assert_not_called()


def test_permission_absent_removes_permissions(salt_functions):
    salt_functions["rabbitmq_management.permission_exist"].return_value = True

    ret = state.permission_absent("/", "myuser")

    assert ret == {
        "name": "/",
        "result": True,
        "changes": {"old": {"vhost": "/", "user": "myuser"}, "new": None},
        "comment": "Permission for user 'myuser' on vhost '/' removed",
    }
    salt_functions["rabbitmq_management.permission_delete"].assert_called_once_with(
        vhost="/", user="myuser"
    )


def test_permission_absent_already_absent(salt_functions):
    ret = state.permission_absent("/", "myuser")

    assert ret == {
        "name": "/",
        "result": True,
        "changes": {},
        "comment": "Permission for user 'myuser' on vhost '/' is already absent",
    }
    salt_functions["rabbitmq_management.permission_delete"].assert_not_called()


def test_permission_absent_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True}, raising=False)
    salt_functions["rabbitmq_management.permission_exist"].return_value = True

    ret = state.permission_absent("/", "myuser")

    assert ret == {
        "name": "/",
        "result": None,
        "changes": {"old": {"vhost": "/", "user": "myuser"}, "new": None},
        "comment": "Permission for user 'myuser' on vhost '/' would be removed",
    }
    salt_functions["rabbitmq_management.permission_delete"].assert_not_called()
