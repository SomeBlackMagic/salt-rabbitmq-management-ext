"""Salt states for managing RabbitMQ bindings."""

import logging

import salt.utils.json

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"

_REQUIRED_FUNCTIONS = (
    "rabbitmq_management.binding_create_queue",
    "rabbitmq_management.binding_create_exchange",
    "rabbitmq_management.binding_delete_queue",
    "rabbitmq_management.binding_delete_exchange",
    "rabbitmq_management.binding_list_queue",
    "rabbitmq_management.binding_list_exchange_source",
)


def __virtual__():
    """Load only when all required RabbitMQ execution functions are available."""
    missing = [function for function in _REQUIRED_FUNCTIONS if function not in __salt__]
    if missing:
        return False, "Required execution functions are not available: {}".format(
            ", ".join(missing)
        )
    return __virtualname__


def _state_return(name):
    """Return an empty Salt state result."""
    return {"name": name, "result": True, "changes": {}, "comment": ""}


def _normalize_arguments(arguments):
    """Normalize binding arguments to a dictionary."""
    if arguments is None:
        return {}
    if isinstance(arguments, str):
        arguments = salt.utils.json.loads(arguments)
    if not isinstance(arguments, dict):
        raise TypeError("arguments must be a dictionary or a JSON object")
    return arguments


def _validate(source, destination, destination_type):
    """Return an error for invalid binding identifiers."""
    if not source:
        return "source is required"
    if not destination:
        return "destination is required"
    if destination_type not in ("queue", "exchange"):
        return "destination_type must be 'queue' or 'exchange'"
    return None


def _binding_data(vhost, source, destination, destination_type, routing_key, arguments):
    """Build the normalized binding representation used in state changes."""
    return {
        "vhost": vhost,
        "source": source,
        "destination": destination,
        "destination_type": destination_type,
        "routing_key": routing_key,
        "arguments": arguments,
    }


def _list_bindings(vhost, source, destination, destination_type, connection_args):
    """Return candidate bindings for the requested destination type."""
    if destination_type == "queue":
        bindings = __salt__["rabbitmq_management.binding_list_queue"](
            vhost, destination, **connection_args
        )
    else:
        bindings = __salt__["rabbitmq_management.binding_list_exchange_source"](
            vhost, source, **connection_args
        )
    if not isinstance(bindings, list):
        raise TypeError("RabbitMQ returned an invalid binding list")
    return bindings


def _find_binding(bindings, source, destination, destination_type, routing_key, arguments):
    """Find a binding that exactly matches the requested identity."""
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        if (
            binding.get("source") == source
            and binding.get("destination") == destination
            and binding.get("destination_type") == destination_type
            and binding.get("routing_key", "") == routing_key
            and _normalize_arguments(binding.get("arguments")) == arguments
        ):
            return binding
    return None


def _get_binding(
    ret,
    vhost,
    source,
    destination,
    destination_type,
    routing_key,
    arguments,
    connection_args,
):
    """Load and find a binding, recording lookup errors in the state return."""
    try:
        bindings = _list_bindings(vhost, source, destination, destination_type, connection_args)
        return _find_binding(
            bindings, source, destination, destination_type, routing_key, arguments
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to list RabbitMQ bindings")
        ret["result"] = False
        ret["comment"] = f"Failed to list bindings: {err}"
        return None


def binding_present(
    name,
    vhost="/",
    source=None,
    destination=None,
    destination_type="queue",
    routing_key="",
    arguments=None,
    **connection_args,
):
    """
    Ensure a RabbitMQ binding exists.

    Args:
        name: State identifier
        vhost: RabbitMQ virtual host
        source: Source exchange name
        destination: Destination queue or exchange name
        destination_type: Destination type (``queue`` or ``exchange``)
        routing_key: Binding routing key
        arguments: Binding arguments as a dictionary or JSON object
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        bind_orders_queue:
          rabbitmq_management.binding_present:
            - name: orders-exchange-to-queue
            - vhost: /production
            - source: orders-exchange
            - destination: orders-queue
            - routing_key: new-order
    """
    ret = _state_return(name)

    validation_error = _validate(source, destination, destination_type)
    if validation_error:
        ret["result"] = False
        ret["comment"] = f"Invalid binding configuration: {validation_error}"
        return ret

    try:
        normalized_arguments = _normalize_arguments(arguments)
    except (TypeError, ValueError) as err:
        ret["result"] = False
        ret["comment"] = f"Invalid binding arguments: {err}"
        return ret

    desired = _binding_data(
        vhost,
        source,
        destination,
        destination_type,
        routing_key,
        normalized_arguments,
    )
    binding = _get_binding(
        ret,
        vhost,
        source,
        destination,
        destination_type,
        routing_key,
        normalized_arguments,
        connection_args,
    )
    if ret["result"] is False:
        return ret
    if binding is not None:
        ret["comment"] = f"Binding '{name}' is already present"
        return ret

    ret["changes"] = {"old": None, "new": desired}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Binding '{name}' would be created"
        return ret

    try:
        if destination_type == "queue":
            __salt__["rabbitmq_management.binding_create_queue"](
                vhost,
                source,
                destination,
                routing_key,
                normalized_arguments,
                **connection_args,
            )
        else:
            __salt__["rabbitmq_management.binding_create_exchange"](
                vhost,
                source,
                destination,
                routing_key,
                normalized_arguments,
                **connection_args,
            )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to create RabbitMQ binding %s", name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to create binding '{name}': {err}"
        return ret

    ret["comment"] = f"Binding '{name}' created"
    return ret


def binding_absent(
    name,
    vhost="/",
    source=None,
    destination=None,
    destination_type="queue",
    routing_key="",
    arguments=None,
    **connection_args,
):
    """
    Ensure a RabbitMQ binding does not exist.

    The matching binding's RabbitMQ ``properties_key`` is used for deletion.

    Args:
        name: State identifier
        vhost: RabbitMQ virtual host
        source: Source exchange name
        destination: Destination queue or exchange name
        destination_type: Destination type (``queue`` or ``exchange``)
        routing_key: Binding routing key
        arguments: Binding arguments as a dictionary or JSON object
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        remove_old_binding:
          rabbitmq_management.binding_absent:
            - name: legacy-orders-binding
            - source: old-exchange
            - destination: orders-queue
            - routing_key: orders
    """
    ret = _state_return(name)

    validation_error = _validate(source, destination, destination_type)
    if validation_error:
        ret["result"] = False
        ret["comment"] = f"Invalid binding configuration: {validation_error}"
        return ret

    try:
        normalized_arguments = _normalize_arguments(arguments)
    except (TypeError, ValueError) as err:
        ret["result"] = False
        ret["comment"] = f"Invalid binding arguments: {err}"
        return ret

    desired = _binding_data(
        vhost,
        source,
        destination,
        destination_type,
        routing_key,
        normalized_arguments,
    )
    binding = _get_binding(
        ret,
        vhost,
        source,
        destination,
        destination_type,
        routing_key,
        normalized_arguments,
        connection_args,
    )
    if ret["result"] is False:
        return ret
    if binding is None:
        ret["comment"] = f"Binding '{name}' is already absent"
        return ret

    properties_key = binding.get("properties_key")
    if properties_key is None:
        ret["result"] = False
        ret["comment"] = "Cannot remove binding: RabbitMQ response has no properties_key"
        return ret

    ret["changes"] = {"old": desired, "new": None}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Binding '{name}' would be removed"
        return ret

    try:
        if destination_type == "queue":
            __salt__["rabbitmq_management.binding_delete_queue"](
                vhost,
                source,
                destination,
                properties_key,
                **connection_args,
            )
        else:
            __salt__["rabbitmq_management.binding_delete_exchange"](
                vhost,
                source,
                destination,
                properties_key,
                **connection_args,
            )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove RabbitMQ binding %s", name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to remove binding '{name}': {err}"
        return ret

    ret["comment"] = f"Binding '{name}' removed"
    return ret
