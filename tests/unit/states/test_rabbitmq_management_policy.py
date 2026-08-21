from unittest.mock import Mock

import pytest

import saltext.rabbitmq_management.states.rabbitmq_management_policy_mod as state


@pytest.fixture
def salt_functions():
    return {
        "rabbitmq_management.policy_create": Mock(return_value={"status": "created"}),
        "rabbitmq_management.policy_delete": Mock(return_value={"status": "deleted"}),
        "rabbitmq_management.policy_exist": Mock(return_value=True),
        "rabbitmq_management.policy_get": Mock(return_value=None),
    }


@pytest.fixture
def configure_loader_modules(salt_functions):
    return {
        state: {
            "__opts__": {"test": False},
            "__salt__": salt_functions,
        }
    }


def _policy(pattern="^.*", definition=None, priority=0, apply_to="all"):
    return {
        "vhost": "/",
        "name": "ha-all",
        "pattern": pattern,
        "definition": definition or {"ha-mode": "all"},
        "priority": priority,
        "apply-to": apply_to,
    }


def test_virtual_requires_execution_functions(salt_functions):
    assert state.__virtual__() == "rabbitmq_management"

    salt_functions.pop("rabbitmq_management.policy_get")

    assert state.__virtual__() == (
        False,
        "Required execution functions are not available: rabbitmq_management.policy_get",
    )


def test_policy_present_creates_new_policy(salt_functions):
    salt_functions["rabbitmq_management.policy_get"].return_value = None

    ret = state.policy_present(
        "ha-all",
        vhost="/",
        pattern="^.*",
        definition={"ha-mode": "all"},
        priority=0,
        apply_to="all",
    )

    assert ret == {
        "name": "ha-all",
        "result": True,
        "changes": {
            "old": None,
            "new": {
                "vhost": "/",
                "name": "ha-all",
                "pattern": "^.*",
                "definition": {"ha-mode": "all"},
                "priority": 0,
                "apply_to": "all",
            },
        },
        "comment": "Policy 'ha-all' created",
    }
    salt_functions["rabbitmq_management.policy_create"].assert_called_once_with(
        "/",
        "ha-all",
        "^.*",
        {"ha-mode": "all"},
        priority=0,
        apply_to="all",
    )


def test_policy_present_no_changes_when_policy_matches(salt_functions):
    salt_functions["rabbitmq_management.policy_get"].return_value = _policy()

    ret = state.policy_present(
        "ha-all",
        vhost="/",
        pattern="^.*",
        definition={"ha-mode": "all"},
        priority=0,
        apply_to="all",
    )

    assert ret == {
        "name": "ha-all",
        "result": True,
        "changes": {},
        "comment": "Policy 'ha-all' is already in the desired state",
    }
    salt_functions["rabbitmq_management.policy_create"].assert_not_called()


def test_policy_present_updates_changed_definition(salt_functions):
    salt_functions["rabbitmq_management.policy_get"].return_value = _policy(
        definition={"ha-mode": "all"}
    )

    ret = state.policy_present(
        "ha-all",
        vhost="/",
        pattern="^.*",
        definition={"ha-mode": "exactly", "ha-params": 2},
        priority=0,
        apply_to="all",
    )

    assert ret == {
        "name": "ha-all",
        "result": True,
        "changes": {
            "old": {"definition": {"ha-mode": "all"}},
            "new": {"definition": {"ha-mode": "exactly", "ha-params": 2}},
        },
        "comment": "Policy 'ha-all' updated",
    }
    salt_functions["rabbitmq_management.policy_create"].assert_called_once()


def test_policy_present_updates_changed_priority(salt_functions):
    salt_functions["rabbitmq_management.policy_get"].return_value = _policy(priority=0)

    ret = state.policy_present(
        "ha-all",
        vhost="/",
        pattern="^.*",
        definition={"ha-mode": "all"},
        priority=10,
        apply_to="all",
    )

    assert ret == {
        "name": "ha-all",
        "result": True,
        "changes": {
            "old": {"priority": 0},
            "new": {"priority": 10},
        },
        "comment": "Policy 'ha-all' updated",
    }
    salt_functions["rabbitmq_management.policy_create"].assert_called_once()


def test_policy_present_handles_json_string_definition(salt_functions):
    salt_functions["rabbitmq_management.policy_get"].return_value = None

    ret = state.policy_present(
        "ha-all",
        vhost="/",
        pattern="^.*",
        definition='{"ha-mode": "all"}',
    )

    assert ret["result"] is True
    assert ret["changes"]["new"]["definition"] == {"ha-mode": "all"}
    salt_functions["rabbitmq_management.policy_create"].assert_called_once_with(
        "/",
        "ha-all",
        "^.*",
        {"ha-mode": "all"},
        priority=0,
        apply_to="all",
    )


def test_policy_present_test_mode_create(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.policy_get"].return_value = None

    ret = state.policy_present(
        "ha-all",
        vhost="/",
        pattern="^.*",
        definition={"ha-mode": "all"},
    )

    assert ret == {
        "name": "ha-all",
        "result": None,
        "changes": {
            "old": None,
            "new": {
                "vhost": "/",
                "name": "ha-all",
                "pattern": "^.*",
                "definition": {"ha-mode": "all"},
                "priority": 0,
                "apply_to": "all",
            },
        },
        "comment": "Policy 'ha-all' would be created",
    }
    salt_functions["rabbitmq_management.policy_create"].assert_not_called()


def test_policy_present_test_mode_update(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.policy_get"].return_value = _policy(priority=0)

    ret = state.policy_present(
        "ha-all",
        vhost="/",
        pattern="^.*",
        definition={"ha-mode": "all"},
        priority=5,
        apply_to="all",
    )

    assert ret == {
        "name": "ha-all",
        "result": None,
        "changes": {
            "old": {"priority": 0},
            "new": {"priority": 5},
        },
        "comment": "Policy 'ha-all' would be updated",
    }
    salt_functions["rabbitmq_management.policy_create"].assert_not_called()


def test_policy_absent_removes_policy(salt_functions):
    salt_functions["rabbitmq_management.policy_exist"].return_value = True

    ret = state.policy_absent("ha-all", vhost="/")

    assert ret == {
        "name": "ha-all",
        "result": True,
        "changes": {"old": "ha-all", "new": None},
        "comment": "Policy 'ha-all' removed",
    }
    salt_functions["rabbitmq_management.policy_delete"].assert_called_once_with("/", "ha-all")


def test_policy_absent_already_absent(salt_functions):
    salt_functions["rabbitmq_management.policy_exist"].return_value = False

    ret = state.policy_absent("ha-all", vhost="/")

    assert ret == {
        "name": "ha-all",
        "result": True,
        "changes": {},
        "comment": "Policy 'ha-all' on vhost '/' is already absent",
    }
    salt_functions["rabbitmq_management.policy_delete"].assert_not_called()


def test_policy_absent_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.policy_exist"].return_value = True

    ret = state.policy_absent("ha-all", vhost="/")

    assert ret == {
        "name": "ha-all",
        "result": None,
        "changes": {"old": "ha-all", "new": None},
        "comment": "Policy 'ha-all' would be removed",
    }
    salt_functions["rabbitmq_management.policy_delete"].assert_not_called()
