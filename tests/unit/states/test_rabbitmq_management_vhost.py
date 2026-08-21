from unittest.mock import Mock

import pytest

import saltext.rabbitmq_management.states.rabbitmq_management_vhost_mod as state


@pytest.fixture
def salt_functions(monkeypatch):
    functions = {
        "rabbitmq_management.vhost_exist": Mock(return_value=False),
        "rabbitmq_management.vhost_get": Mock(),
        "rabbitmq_management.vhost_create": Mock(return_value={"status": "created"}),
        "rabbitmq_management.vhost_delete": Mock(return_value={"status": "deleted"}),
    }
    monkeypatch.setattr(state, "__salt__", functions, raising=False)
    monkeypatch.setattr(state, "__opts__", {"test": False}, raising=False)
    return functions


def test_virtual_requires_real_execution_functions(salt_functions):
    assert state.__virtual__() == "rabbitmq_management"

    salt_functions.pop("rabbitmq_management.vhost_get")

    assert state.__virtual__() == (
        False,
        "Required execution functions are not available: rabbitmq_management.vhost_get",
    )


def test_vhost_present_creates_vhost_with_normalized_configuration(salt_functions):
    ret = state.vhost_present(
        "/production",
        description="Production",
        tags="production, critical",
        default_queue_type="quorum",
        tracing=False,
        timeout=10,
    )

    assert ret == {
        "name": "/production",
        "result": True,
        "changes": {
            "old": None,
            "new": {
                "name": "/production",
                "description": "Production",
                "tags": ["production", "critical"],
                "default_queue_type": "quorum",
                "tracing": False,
            },
        },
        "comment": "Vhost '/production' created",
    }
    salt_functions["rabbitmq_management.vhost_create"].assert_called_once_with(
        "/production",
        description="Production",
        tags=["production", "critical"],
        default_queue_type="quorum",
        tracing=False,
        timeout=10,
    )


def test_vhost_present_is_idempotent_and_ignores_tag_order(salt_functions):
    salt_functions["rabbitmq_management.vhost_exist"].return_value = True
    salt_functions["rabbitmq_management.vhost_get"].return_value = {
        "description": "Production",
        "tags": ["critical", "production"],
        "default_queue_type": "quorum",
        "tracing": False,
    }

    ret = state.vhost_present(
        "/production",
        description="Production",
        tags=["production", "critical"],
        default_queue_type="quorum",
        tracing=False,
    )

    assert ret["result"] is True
    assert not ret["changes"]
    salt_functions["rabbitmq_management.vhost_create"].assert_not_called()


def test_vhost_present_can_clear_description_and_tags(salt_functions):
    salt_functions["rabbitmq_management.vhost_exist"].return_value = True
    salt_functions["rabbitmq_management.vhost_get"].return_value = {
        "description": "Old description",
        "tags": ["old"],
        "tracing": True,
    }

    ret = state.vhost_present("/production", description="", tags=[])

    assert ret["changes"] == {
        "old": {"description": "Old description", "tags": ["old"]},
        "new": {"description": "", "tags": []},
    }
    salt_functions["rabbitmq_management.vhost_create"].assert_called_once_with(
        "/production", description="", tags=[]
    )


def test_vhost_present_detects_missing_default_queue_type(salt_functions):
    salt_functions["rabbitmq_management.vhost_exist"].return_value = True
    salt_functions["rabbitmq_management.vhost_get"].return_value = {"name": "/production"}

    ret = state.vhost_present("/production", default_queue_type="quorum")

    assert ret["changes"] == {
        "old": {"default_queue_type": None},
        "new": {"default_queue_type": "quorum"},
    }


def test_vhost_present_test_mode_reports_exact_changes(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.vhost_exist"].return_value = True
    salt_functions["rabbitmq_management.vhost_get"].return_value = {"tracing": True}

    ret = state.vhost_present("/production", tracing=False)

    assert ret["result"] is None
    assert ret["changes"] == {"old": {"tracing": True}, "new": {"tracing": False}}
    salt_functions["rabbitmq_management.vhost_create"].assert_not_called()


def test_vhost_present_rejects_unreadable_current_configuration(salt_functions):
    salt_functions["rabbitmq_management.vhost_exist"].return_value = True
    salt_functions["rabbitmq_management.vhost_get"].return_value = None

    ret = state.vhost_present("/production", tracing=False)

    assert ret["result"] is False
    assert "could not be retrieved" in ret["comment"]


def test_vhost_absent_is_idempotent(salt_functions):
    ret = state.vhost_absent("/old")

    assert ret == {
        "name": "/old",
        "result": True,
        "changes": {},
        "comment": "Vhost '/old' is already absent",
    }
    salt_functions["rabbitmq_management.vhost_delete"].assert_not_called()


def test_vhost_absent_removes_existing_vhost(salt_functions):
    salt_functions["rabbitmq_management.vhost_exist"].return_value = True

    ret = state.vhost_absent("/old", timeout=10)

    assert ret["result"] is True
    assert ret["changes"] == {"old": "/old", "new": None}
    salt_functions["rabbitmq_management.vhost_delete"].assert_called_once_with("/old", timeout=10)
