from unittest.mock import Mock

import pytest
import salt.utils.sdb

import saltext.rabbitmq_management.states.rabbitmq_management_user_mod as state


@pytest.fixture
def salt_functions(monkeypatch):
    functions = {
        "rabbitmq_management.user_create": Mock(return_value={"status": "created"}),
        "rabbitmq_management.user_delete": Mock(return_value={"status": "deleted"}),
        "rabbitmq_management.user_exist": Mock(return_value=False),
        "rabbitmq_management.user_get": Mock(return_value=None),
        "rabbitmq_management.user_limit_get": Mock(return_value=None),
        "rabbitmq_management.user_limit_set": Mock(return_value=True),
        "rabbitmq_management.user_limit_delete": Mock(return_value=True),
        "rabbitmq_management.user_limit_exist": Mock(return_value=False),
    }
    monkeypatch.setattr(state, "__salt__", functions, raising=False)
    monkeypatch.setattr(state, "__opts__", {"test": False}, raising=False)
    return functions


def test_virtual_requires_execution_functions(salt_functions):
    assert state.__virtual__() == "rabbitmq_management"

    salt_functions.pop("rabbitmq_management.user_get")

    assert state.__virtual__() == (
        False,
        "Required execution functions are not available: rabbitmq_management.user_get",
    )


def test_user_present_creates_new_user(salt_functions):
    ret = state.user_present(
        "myapp",
        password="secret",
        tags="monitoring, management",
        hashing_algorithm="rabbit_password_hashing_sha256",
        timeout=10,
    )

    assert ret == {
        "name": "myapp",
        "result": True,
        "changes": {
            "old": None,
            "new": {
                "name": "myapp",
                "tags": ["monitoring", "management"],
                "password_set": True,
            },
        },
        "comment": "User 'myapp' created",
    }
    assert "secret" not in repr(ret)
    salt_functions["rabbitmq_management.user_get"].assert_called_once_with("myapp", timeout=10)
    salt_functions["rabbitmq_management.user_create"].assert_called_once_with(
        "myapp",
        password="secret",
        tags=["monitoring", "management"],
        hashing_algorithm="rabbit_password_hashing_sha256",
        timeout=10,
    )


def test_user_present_no_changes_when_tags_match(salt_functions):
    salt_functions["rabbitmq_management.user_get"].return_value = {
        "name": "myapp",
        "tags": "management,monitoring",
    }

    ret = state.user_present("myapp", tags=["monitoring", "management"])

    assert ret == {
        "name": "myapp",
        "result": True,
        "changes": {},
        "comment": "User 'myapp' already exists with the correct configuration",
    }
    salt_functions["rabbitmq_management.user_create"].assert_not_called()


def test_user_present_does_not_manage_omitted_fields(salt_functions):
    salt_functions["rabbitmq_management.user_get"].return_value = {
        "name": "myapp",
        "tags": ["administrator"],
    }

    ret = state.user_present("myapp")

    assert ret["result"] is True
    assert not ret["changes"]
    salt_functions["rabbitmq_management.user_create"].assert_not_called()


def test_user_present_updates_tags(salt_functions):
    salt_functions["rabbitmq_management.user_get"].return_value = {
        "name": "myapp",
        "tags": ["management"],
    }

    ret = state.user_present("myapp", tags="monitoring, management", timeout=10)

    assert ret == {
        "name": "myapp",
        "result": True,
        "changes": {
            "old": {"tags": ["management"]},
            "new": {"tags": ["monitoring", "management"]},
        },
        "comment": "User 'myapp' updated",
    }
    salt_functions["rabbitmq_management.user_create"].assert_called_once_with(
        "myapp",
        password=None,
        tags=["monitoring", "management"],
        hashing_algorithm=None,
        timeout=10,
    )


def test_user_present_updates_password_without_exposing_it(salt_functions):
    salt_functions["rabbitmq_management.user_get"].return_value = {
        "name": "myapp",
        "tags": ["management"],
    }

    ret = state.user_present("myapp", password="new-secret")

    assert ret["changes"] == {
        "old": {"password_set": None},
        "new": {"password_set": True},
    }
    assert "new-secret" not in repr(ret)
    salt_functions["rabbitmq_management.user_create"].assert_called_once_with(
        "myapp",
        password="new-secret",
        tags=None,
        hashing_algorithm=None,
    )


def test_user_present_resolves_password_from_sdb(salt_functions, monkeypatch):
    sdb_get = Mock(return_value="resolved-secret")
    monkeypatch.setattr(salt.utils.sdb, "sdb_get", sdb_get)

    ret = state.user_present("myapp", password="sdb://vault/rabbitmq/myapp")

    sdb_get.assert_called_once_with("sdb://vault/rabbitmq/myapp", state.__opts__, strict=True)
    salt_functions["rabbitmq_management.user_create"].assert_called_once_with(
        "myapp",
        password="resolved-secret",
        tags=None,
        hashing_algorithm=None,
    )
    assert "resolved-secret" not in repr(ret)
    assert "sdb://vault/rabbitmq/myapp" not in repr(ret)


def test_user_present_does_not_resolve_plain_password(salt_functions, monkeypatch):
    sdb_get = Mock()
    monkeypatch.setattr(salt.utils.sdb, "sdb_get", sdb_get)

    state.user_present("myapp", password="plain-secret")

    sdb_get.assert_not_called()
    salt_functions["rabbitmq_management.user_create"].assert_called_once_with(
        "myapp",
        password="plain-secret",
        tags=None,
        hashing_algorithm=None,
    )


def test_user_present_does_not_resolve_sdb_password_in_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    sdb_get = Mock(return_value="resolved-secret")
    monkeypatch.setattr(salt.utils.sdb, "sdb_get", sdb_get)

    ret = state.user_present("myapp", password="sdb://vault/rabbitmq/myapp")

    assert ret["result"] is None
    assert ret["changes"]["new"]["password_set"] is True
    assert "resolved-secret" not in repr(ret)
    assert "sdb://vault/rabbitmq/myapp" not in repr(ret)
    sdb_get.assert_not_called()
    salt_functions["rabbitmq_management.user_create"].assert_not_called()


def test_user_present_reports_sdb_failure(salt_functions, monkeypatch):
    sdb_get = Mock(side_effect=RuntimeError("Vault unavailable"))
    monkeypatch.setattr(salt.utils.sdb, "sdb_get", sdb_get)

    ret = state.user_present("myapp", password="sdb://vault/rabbitmq/myapp")

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"] == "Failed to resolve password from SDB for user 'myapp'"
    salt_functions["rabbitmq_management.user_create"].assert_not_called()


@pytest.mark.parametrize("sdb_value", [None, {"password": "secret"}])
def test_user_present_rejects_invalid_sdb_password(salt_functions, monkeypatch, sdb_value):
    monkeypatch.setattr(salt.utils.sdb, "sdb_get", Mock(return_value=sdb_value))

    ret = state.user_present("myapp", password="sdb://vault/rabbitmq/myapp")

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"] == "Failed to resolve password from SDB for user 'myapp'"
    salt_functions["rabbitmq_management.user_create"].assert_not_called()


def test_user_present_test_mode_create(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})

    ret = state.user_present("myapp", password="secret", tags="monitoring")

    assert ret == {
        "name": "myapp",
        "result": None,
        "changes": {
            "old": None,
            "new": {
                "name": "myapp",
                "tags": ["monitoring"],
                "password_set": True,
            },
        },
        "comment": "User 'myapp' would be created",
    }
    assert "secret" not in repr(ret)
    salt_functions["rabbitmq_management.user_create"].assert_not_called()


def test_user_present_test_mode_update(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.user_get"].return_value = {
        "name": "myapp",
        "tags": ["management"],
    }

    ret = state.user_present("myapp", password="secret", tags="monitoring")

    assert ret == {
        "name": "myapp",
        "result": None,
        "changes": {
            "old": {"tags": ["management"], "password_set": None},
            "new": {"tags": ["monitoring"], "password_set": True},
        },
        "comment": "User 'myapp' would be updated",
    }
    assert "secret" not in repr(ret)
    salt_functions["rabbitmq_management.user_create"].assert_not_called()


def test_user_absent_removes_user(salt_functions):
    salt_functions["rabbitmq_management.user_exist"].return_value = True

    ret = state.user_absent("olduser", timeout=10)

    assert ret == {
        "name": "olduser",
        "result": True,
        "changes": {"old": "olduser", "new": None},
        "comment": "User 'olduser' removed",
    }
    salt_functions["rabbitmq_management.user_exist"].assert_called_once_with("olduser", timeout=10)
    salt_functions["rabbitmq_management.user_delete"].assert_called_once_with("olduser", timeout=10)


def test_user_absent_already_absent(salt_functions):
    ret = state.user_absent("olduser")

    assert ret == {
        "name": "olduser",
        "result": True,
        "changes": {},
        "comment": "User 'olduser' is already absent",
    }
    salt_functions["rabbitmq_management.user_delete"].assert_not_called()


def test_user_absent_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.user_exist"].return_value = True

    ret = state.user_absent("olduser")

    assert ret == {
        "name": "olduser",
        "result": None,
        "changes": {"old": "olduser", "new": None},
        "comment": "User 'olduser' would be removed",
    }
    salt_functions["rabbitmq_management.user_delete"].assert_not_called()


def test_user_present_reports_lookup_failure(salt_functions):
    salt_functions["rabbitmq_management.user_get"].side_effect = RuntimeError("API unavailable")

    ret = state.user_present("myapp")

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"] == "Failed to get user 'myapp': API unavailable"


def test_user_present_rejects_invalid_tags(salt_functions):
    ret = state.user_present("myapp", tags={"monitoring"})

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"].startswith("Invalid user configuration:")
    salt_functions["rabbitmq_management.user_get"].assert_not_called()


def test_user_present_rejects_unreadable_current_configuration(salt_functions):
    salt_functions["rabbitmq_management.user_get"].return_value = ["myapp"]

    ret = state.user_present("myapp", tags="monitoring")

    assert ret["result"] is False
    assert not ret["changes"]
    assert "could not be retrieved" in ret["comment"]
    salt_functions["rabbitmq_management.user_create"].assert_not_called()


def test_user_present_rejects_invalid_current_tags(salt_functions):
    salt_functions["rabbitmq_management.user_get"].return_value = {
        "name": "myapp",
        "tags": {"monitoring"},
    }

    ret = state.user_present("myapp", tags="monitoring")

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"].startswith("Invalid user configuration returned by RabbitMQ:")
    salt_functions["rabbitmq_management.user_create"].assert_not_called()


def test_user_present_reports_create_failure(salt_functions):
    salt_functions["rabbitmq_management.user_create"].side_effect = RuntimeError("API unavailable")

    ret = state.user_present("myapp")

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"] == "Failed to create/update user 'myapp': API unavailable"


def test_user_absent_reports_delete_failure(salt_functions):
    salt_functions["rabbitmq_management.user_exist"].return_value = True
    salt_functions["rabbitmq_management.user_delete"].side_effect = RuntimeError("API unavailable")

    ret = state.user_absent("olduser")

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"] == "Failed to remove user 'olduser': API unavailable"


def test_user_absent_reports_existence_check_failure(salt_functions):
    salt_functions["rabbitmq_management.user_exist"].side_effect = RuntimeError("API unavailable")

    ret = state.user_absent("olduser")

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"] == "Failed to check user existence: API unavailable"
    salt_functions["rabbitmq_management.user_delete"].assert_not_called()


def test_user_limit_present_sets_new_limit(salt_functions):
    salt_functions["rabbitmq_management.user_limit_get"].return_value = None

    ret = state.user_limit_present("myapp", limit_type="max-channels", value=100)

    assert ret == {
        "name": "myapp",
        "result": True,
        "changes": {"old": None, "new": {"limit_type": "max-channels", "value": 100}},
        "comment": "Limit 'max-channels' for user 'myapp' set",
    }
    salt_functions["rabbitmq_management.user_limit_set"].assert_called_once_with(
        "myapp", "max-channels", 100
    )


def test_user_limit_present_no_changes_when_value_matches(salt_functions):
    salt_functions["rabbitmq_management.user_limit_get"].return_value = {
        "user": "myapp",
        "name": "max-channels",
        "value": 100,
    }

    ret = state.user_limit_present("myapp", limit_type="max-channels", value=100)

    assert ret == {
        "name": "myapp",
        "result": True,
        "changes": {},
        "comment": "Limit 'max-channels' for user 'myapp' is already in the desired state",
    }
    salt_functions["rabbitmq_management.user_limit_set"].assert_not_called()


def test_user_limit_present_updates_changed_value(salt_functions):
    salt_functions["rabbitmq_management.user_limit_get"].return_value = {
        "user": "myapp",
        "name": "max-channels",
        "value": 50,
    }

    ret = state.user_limit_present("myapp", limit_type="max-channels", value=100)

    assert ret == {
        "name": "myapp",
        "result": True,
        "changes": {"old": {"value": 50}, "new": {"value": 100}},
        "comment": "Limit 'max-channels' for user 'myapp' updated",
    }
    salt_functions["rabbitmq_management.user_limit_set"].assert_called_once_with(
        "myapp", "max-channels", 100
    )


def test_user_limit_present_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.user_limit_get"].return_value = None

    ret = state.user_limit_present("myapp", limit_type="max-channels", value=100)

    assert ret == {
        "name": "myapp",
        "result": None,
        "changes": {"old": None, "new": {"limit_type": "max-channels", "value": 100}},
        "comment": "Limit 'max-channels' for user 'myapp' would be set",
    }
    salt_functions["rabbitmq_management.user_limit_set"].assert_not_called()


def test_user_limit_absent_removes_limit(salt_functions):
    salt_functions["rabbitmq_management.user_limit_get"].return_value = {
        "user": "myapp",
        "name": "max-channels",
        "value": 100,
    }

    ret = state.user_limit_absent("myapp", limit_type="max-channels")

    assert ret == {
        "name": "myapp",
        "result": True,
        "changes": {"old": {"limit_type": "max-channels", "value": 100}, "new": None},
        "comment": "Limit 'max-channels' for user 'myapp' removed",
    }
    salt_functions["rabbitmq_management.user_limit_delete"].assert_called_once_with(
        "myapp", "max-channels"
    )


def test_user_limit_absent_already_absent(salt_functions):
    salt_functions["rabbitmq_management.user_limit_get"].return_value = None

    ret = state.user_limit_absent("myapp", limit_type="max-channels")

    assert ret == {
        "name": "myapp",
        "result": True,
        "changes": {},
        "comment": "Limit 'max-channels' for user 'myapp' is already absent",
    }
    salt_functions["rabbitmq_management.user_limit_delete"].assert_not_called()


def test_user_limit_absent_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.user_limit_get"].return_value = {
        "user": "myapp",
        "name": "max-channels",
        "value": 100,
    }

    ret = state.user_limit_absent("myapp", limit_type="max-channels")

    assert ret == {
        "name": "myapp",
        "result": None,
        "changes": {"old": {"limit_type": "max-channels", "value": 100}, "new": None},
        "comment": "Limit 'max-channels' for user 'myapp' would be removed",
    }
    salt_functions["rabbitmq_management.user_limit_delete"].assert_not_called()
