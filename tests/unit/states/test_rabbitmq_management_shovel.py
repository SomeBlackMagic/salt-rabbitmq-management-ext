from unittest.mock import Mock

import pytest

import saltext.rabbitmq_management.states.rabbitmq_management_shovel_mod as state


@pytest.fixture
def salt_functions():
    return {
        "rabbitmq_management.shovel_create": Mock(return_value={"status": "created"}),
        "rabbitmq_management.shovel_delete": Mock(return_value=True),
        "rabbitmq_management.shovel_exist": Mock(return_value=True),
        "rabbitmq_management.shovel_get": Mock(return_value=None),
    }


@pytest.fixture
def configure_loader_modules(salt_functions):
    return {
        state: {
            "__opts__": {"test": False},
            "__salt__": salt_functions,
        }
    }


def _shovel(**extra_value):
    value = {
        "src-uri": "amqp://source",
        "src-queue": "source-queue",
        "dest-uri": "amqp://destination",
        "dest-queue": "dest-queue",
    }
    value.update(extra_value)
    return {
        "component": "shovel",
        "vhost": "/",
        "name": "my-shovel",
        "value": value,
    }


def test_virtual_requires_execution_functions(salt_functions):
    assert state.__virtual__() == "rabbitmq_management"

    salt_functions.pop("rabbitmq_management.shovel_get")

    assert state.__virtual__() == (
        False,
        "Required execution functions are not available: rabbitmq_management.shovel_get",
    )


def test_shovel_present_creates_new_shovel(salt_functions):
    salt_functions["rabbitmq_management.shovel_get"].return_value = None

    ret = state.shovel_present(
        "my-shovel",
        vhost="/",
        src_uri="amqp://source",
        src_queue="source-queue",
        dest_uri="amqp://destination",
        dest_queue="dest-queue",
        prefetch_count=100,
    )

    assert ret == {
        "name": "my-shovel",
        "result": True,
        "changes": {
            "old": None,
            "new": {
                "vhost": "/",
                "name": "my-shovel",
                "value": {
                    "src-uri": "amqp://source",
                    "src-queue": "source-queue",
                    "dest-uri": "amqp://destination",
                    "dest-queue": "dest-queue",
                    "prefetch-count": 100,
                },
            },
        },
        "comment": "Shovel 'my-shovel' created",
    }
    salt_functions["rabbitmq_management.shovel_create"].assert_called_once_with(
        "/",
        "my-shovel",
        src_uri="amqp://source",
        src_queue="source-queue",
        dest_uri="amqp://destination",
        dest_queue="dest-queue",
        prefetch_count=100,
        reconnect_delay=None,
        ack_mode=None,
        src_delete_after=None,
    )


def test_shovel_present_no_changes_when_value_matches(salt_functions):
    salt_functions["rabbitmq_management.shovel_get"].return_value = _shovel(
        **{"prefetch-count": 100}
    )

    ret = state.shovel_present(
        "my-shovel",
        vhost="/",
        src_uri="amqp://source",
        src_queue="source-queue",
        dest_uri="amqp://destination",
        dest_queue="dest-queue",
        prefetch_count=100,
    )

    assert ret == {
        "name": "my-shovel",
        "result": True,
        "changes": {},
        "comment": "Shovel 'my-shovel' is already in the desired state",
    }
    salt_functions["rabbitmq_management.shovel_create"].assert_not_called()


def test_shovel_present_updates_changed_value(salt_functions):
    salt_functions["rabbitmq_management.shovel_get"].return_value = _shovel(
        **{"prefetch-count": 50}
    )

    ret = state.shovel_present(
        "my-shovel",
        vhost="/",
        src_uri="amqp://source",
        src_queue="source-queue",
        dest_uri="amqp://destination",
        dest_queue="dest-queue",
        prefetch_count=100,
    )

    assert ret == {
        "name": "my-shovel",
        "result": True,
        "changes": {
            "old": {
                "value": {
                    "src-uri": "amqp://source",
                    "src-queue": "source-queue",
                    "dest-uri": "amqp://destination",
                    "dest-queue": "dest-queue",
                    "prefetch-count": 50,
                }
            },
            "new": {
                "value": {
                    "src-uri": "amqp://source",
                    "src-queue": "source-queue",
                    "dest-uri": "amqp://destination",
                    "dest-queue": "dest-queue",
                    "prefetch-count": 100,
                }
            },
        },
        "comment": "Shovel 'my-shovel' updated",
    }
    salt_functions["rabbitmq_management.shovel_create"].assert_called_once()


def test_shovel_present_test_mode_create(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.shovel_get"].return_value = None

    ret = state.shovel_present(
        "my-shovel",
        vhost="/",
        src_uri="amqp://source",
        src_queue="source-queue",
        dest_uri="amqp://destination",
        dest_queue="dest-queue",
    )

    assert ret == {
        "name": "my-shovel",
        "result": None,
        "changes": {
            "old": None,
            "new": {
                "vhost": "/",
                "name": "my-shovel",
                "value": {
                    "src-uri": "amqp://source",
                    "src-queue": "source-queue",
                    "dest-uri": "amqp://destination",
                    "dest-queue": "dest-queue",
                },
            },
        },
        "comment": "Shovel 'my-shovel' would be created",
    }
    salt_functions["rabbitmq_management.shovel_create"].assert_not_called()


def test_shovel_present_test_mode_update(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.shovel_get"].return_value = _shovel(
        **{"ack-mode": "no-ack"}
    )

    ret = state.shovel_present(
        "my-shovel",
        vhost="/",
        src_uri="amqp://source",
        src_queue="source-queue",
        dest_uri="amqp://destination",
        dest_queue="dest-queue",
        ack_mode="on-confirm",
    )

    assert ret == {
        "name": "my-shovel",
        "result": None,
        "changes": {
            "old": {
                "value": {
                    "src-uri": "amqp://source",
                    "src-queue": "source-queue",
                    "dest-uri": "amqp://destination",
                    "dest-queue": "dest-queue",
                    "ack-mode": "no-ack",
                }
            },
            "new": {
                "value": {
                    "src-uri": "amqp://source",
                    "src-queue": "source-queue",
                    "dest-uri": "amqp://destination",
                    "dest-queue": "dest-queue",
                    "ack-mode": "on-confirm",
                }
            },
        },
        "comment": "Shovel 'my-shovel' would be updated",
    }
    salt_functions["rabbitmq_management.shovel_create"].assert_not_called()


def test_shovel_absent_removes_shovel(salt_functions):
    salt_functions["rabbitmq_management.shovel_exist"].return_value = True

    ret = state.shovel_absent("my-shovel", vhost="/")

    assert ret == {
        "name": "my-shovel",
        "result": True,
        "changes": {"old": "my-shovel", "new": None},
        "comment": "Shovel 'my-shovel' removed",
    }
    salt_functions["rabbitmq_management.shovel_delete"].assert_called_once_with("/", "my-shovel")


def test_shovel_absent_already_absent(salt_functions):
    salt_functions["rabbitmq_management.shovel_exist"].return_value = False

    ret = state.shovel_absent("my-shovel", vhost="/")

    assert ret == {
        "name": "my-shovel",
        "result": True,
        "changes": {},
        "comment": "Shovel 'my-shovel' on vhost '/' is already absent",
    }
    salt_functions["rabbitmq_management.shovel_delete"].assert_not_called()


def test_shovel_absent_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.shovel_exist"].return_value = True

    ret = state.shovel_absent("my-shovel", vhost="/")

    assert ret == {
        "name": "my-shovel",
        "result": None,
        "changes": {"old": "my-shovel", "new": None},
        "comment": "Shovel 'my-shovel' would be removed",
    }
    salt_functions["rabbitmq_management.shovel_delete"].assert_not_called()
