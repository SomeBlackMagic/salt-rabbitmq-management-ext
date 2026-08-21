from unittest.mock import Mock

import pytest

import saltext.rabbitmq_management.states.rabbitmq_management_binding_mod as state


@pytest.fixture
def salt_functions():
    return {
        "rabbitmq_management.binding_create_queue": Mock(return_value={"status": "created"}),
        "rabbitmq_management.binding_create_exchange": Mock(return_value={"status": "created"}),
        "rabbitmq_management.binding_delete_queue": Mock(return_value={"status": "deleted"}),
        "rabbitmq_management.binding_delete_exchange": Mock(return_value={"status": "deleted"}),
        "rabbitmq_management.binding_list_queue": Mock(return_value=[]),
        "rabbitmq_management.binding_list_exchange_source": Mock(return_value=[]),
    }


@pytest.fixture
def configure_loader_modules(salt_functions):
    return {
        state: {
            "__opts__": {"test": False},
            "__salt__": salt_functions,
        }
    }


def _binding(destination_type="queue", arguments=None, properties_key="orders"):
    return {
        "vhost": "/",
        "source": "orders-exchange",
        "destination": "orders-queue",
        "destination_type": destination_type,
        "routing_key": "orders",
        "arguments": arguments or {},
        "properties_key": properties_key,
    }


def _binding_changes(destination_type="queue", arguments=None):
    return {
        "vhost": "/",
        "source": "orders-exchange",
        "destination": "orders-queue",
        "destination_type": destination_type,
        "routing_key": "orders",
        "arguments": arguments or {},
    }


def test_virtual_requires_execution_functions(salt_functions):
    assert state.__virtual__() == "rabbitmq_management"

    salt_functions.pop("rabbitmq_management.binding_delete_exchange")

    assert state.__virtual__() == (
        False,
        "Required execution functions are not available: "
        "rabbitmq_management.binding_delete_exchange",
    )


def test_binding_present_creates_queue_binding(salt_functions):
    ret = state.binding_present(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        routing_key="orders",
        timeout=10,
    )

    assert ret == {
        "name": "orders-binding",
        "result": True,
        "changes": {"old": None, "new": _binding_changes()},
        "comment": "Binding 'orders-binding' created",
    }
    salt_functions["rabbitmq_management.binding_list_queue"].assert_called_once_with(
        "/", "orders-queue", timeout=10
    )
    salt_functions["rabbitmq_management.binding_create_queue"].assert_called_once_with(
        "/", "orders-exchange", "orders-queue", "orders", {}, timeout=10
    )


def test_binding_present_creates_exchange_binding(salt_functions):
    ret = state.binding_present(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        destination_type="exchange",
        routing_key="orders",
    )

    assert ret["changes"] == {
        "old": None,
        "new": _binding_changes(destination_type="exchange"),
    }
    salt_functions["rabbitmq_management.binding_list_exchange_source"].assert_called_once_with(
        "/", "orders-exchange"
    )
    salt_functions["rabbitmq_management.binding_create_exchange"].assert_called_once_with(
        "/", "orders-exchange", "orders-queue", "orders", {}
    )


def test_binding_present_no_changes_when_binding_exists(salt_functions):
    salt_functions["rabbitmq_management.binding_list_queue"].return_value = [_binding()]

    ret = state.binding_present(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        routing_key="orders",
        arguments=None,
    )

    assert ret == {
        "name": "orders-binding",
        "result": True,
        "changes": {},
        "comment": "Binding 'orders-binding' is already present",
    }
    salt_functions["rabbitmq_management.binding_create_queue"].assert_not_called()


def test_binding_present_normalizes_json_arguments(salt_functions):
    arguments = {"x-match": "all", "type": "order"}
    salt_functions["rabbitmq_management.binding_list_queue"].return_value = [
        _binding(arguments=arguments, properties_key="orders~hash")
    ]

    ret = state.binding_present(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        routing_key="orders",
        arguments='{"x-match": "all", "type": "order"}',
    )

    assert ret["result"] is True
    assert not ret["changes"]
    salt_functions["rabbitmq_management.binding_create_queue"].assert_not_called()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"destination": "orders-queue"}, "source is required"),
        ({"source": "orders-exchange"}, "destination is required"),
        (
            {
                "source": "orders-exchange",
                "destination": "orders-queue",
                "destination_type": "stream",
            },
            "destination_type must be 'queue' or 'exchange'",
        ),
    ],
)
def test_binding_present_rejects_invalid_parameters(salt_functions, kwargs, message):
    ret = state.binding_present("orders-binding", **kwargs)

    assert ret["result"] is False
    assert not ret["changes"]
    assert message in ret["comment"]
    salt_functions["rabbitmq_management.binding_list_queue"].assert_not_called()
    salt_functions["rabbitmq_management.binding_list_exchange_source"].assert_not_called()


def test_binding_present_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})

    ret = state.binding_present(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        routing_key="orders",
    )

    assert ret == {
        "name": "orders-binding",
        "result": None,
        "changes": {"old": None, "new": _binding_changes()},
        "comment": "Binding 'orders-binding' would be created",
    }
    salt_functions["rabbitmq_management.binding_create_queue"].assert_not_called()


def test_binding_absent_removes_queue_binding(salt_functions):
    salt_functions["rabbitmq_management.binding_list_queue"].return_value = [_binding()]

    ret = state.binding_absent(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        routing_key="orders",
        timeout=10,
    )

    assert ret == {
        "name": "orders-binding",
        "result": True,
        "changes": {"old": _binding_changes(), "new": None},
        "comment": "Binding 'orders-binding' removed",
    }
    salt_functions["rabbitmq_management.binding_delete_queue"].assert_called_once_with(
        "/", "orders-exchange", "orders-queue", "orders", timeout=10
    )


def test_binding_absent_removes_exchange_binding(salt_functions):
    salt_functions["rabbitmq_management.binding_list_exchange_source"].return_value = [
        _binding(destination_type="exchange")
    ]

    ret = state.binding_absent(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        destination_type="exchange",
        routing_key="orders",
    )

    assert ret["changes"] == {
        "old": _binding_changes(destination_type="exchange"),
        "new": None,
    }
    salt_functions["rabbitmq_management.binding_delete_exchange"].assert_called_once_with(
        "/", "orders-exchange", "orders-queue", "orders"
    )


def test_binding_absent_already_absent(salt_functions):
    ret = state.binding_absent(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        routing_key="orders",
    )

    assert ret == {
        "name": "orders-binding",
        "result": True,
        "changes": {},
        "comment": "Binding 'orders-binding' is already absent",
    }
    salt_functions["rabbitmq_management.binding_delete_queue"].assert_not_called()


def test_binding_absent_uses_properties_key_from_list(salt_functions):
    arguments = {"x-match": "all", "type": "order"}
    salt_functions["rabbitmq_management.binding_list_queue"].return_value = [
        _binding(arguments=arguments, properties_key="orders~DkLlKQ")
    ]

    state.binding_absent(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        routing_key="orders",
        arguments=arguments,
    )

    salt_functions["rabbitmq_management.binding_delete_queue"].assert_called_once_with(
        "/", "orders-exchange", "orders-queue", "orders~DkLlKQ"
    )


def test_binding_absent_test_mode(salt_functions, monkeypatch):
    monkeypatch.setattr(state, "__opts__", {"test": True})
    salt_functions["rabbitmq_management.binding_list_queue"].return_value = [_binding()]

    ret = state.binding_absent(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        routing_key="orders",
    )

    assert ret == {
        "name": "orders-binding",
        "result": None,
        "changes": {"old": _binding_changes(), "new": None},
        "comment": "Binding 'orders-binding' would be removed",
    }
    salt_functions["rabbitmq_management.binding_delete_queue"].assert_not_called()


def test_binding_present_reports_list_failure(salt_functions):
    salt_functions["rabbitmq_management.binding_list_queue"].side_effect = RuntimeError(
        "API unavailable"
    )

    ret = state.binding_present(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
    )

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"] == "Failed to list bindings: API unavailable"


def test_binding_present_rejects_invalid_json_arguments(salt_functions):
    ret = state.binding_present(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        arguments="not-json",
    )

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"].startswith("Invalid binding arguments:")
    salt_functions["rabbitmq_management.binding_list_queue"].assert_not_called()


def test_binding_present_reports_create_failure(salt_functions):
    salt_functions["rabbitmq_management.binding_create_queue"].side_effect = RuntimeError(
        "API unavailable"
    )

    ret = state.binding_present(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
    )

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"] == "Failed to create binding 'orders-binding': API unavailable"


def test_binding_absent_rejects_binding_without_properties_key(salt_functions):
    binding = _binding()
    binding.pop("properties_key")
    salt_functions["rabbitmq_management.binding_list_queue"].return_value = [binding]

    ret = state.binding_absent(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        routing_key="orders",
    )

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"] == "Cannot remove binding: RabbitMQ response has no properties_key"
    salt_functions["rabbitmq_management.binding_delete_queue"].assert_not_called()


def test_binding_absent_reports_delete_failure(salt_functions):
    salt_functions["rabbitmq_management.binding_list_queue"].return_value = [_binding()]
    salt_functions["rabbitmq_management.binding_delete_queue"].side_effect = RuntimeError(
        "API unavailable"
    )

    ret = state.binding_absent(
        "orders-binding",
        source="orders-exchange",
        destination="orders-queue",
        routing_key="orders",
    )

    assert ret["result"] is False
    assert not ret["changes"]
    assert ret["comment"] == "Failed to remove binding 'orders-binding': API unavailable"
