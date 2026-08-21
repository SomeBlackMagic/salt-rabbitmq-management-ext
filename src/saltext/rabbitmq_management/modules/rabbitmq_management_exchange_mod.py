"""RabbitMQ exchange management via the Management API."""

from urllib.parse import quote

import salt.utils.json
from salt.exceptions import CommandExecutionError

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _http_request

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


# =============================================================================
# Exchanges Management (HTTP API)
# =============================================================================


def exchange_list(vhost="/", **config_override):
    """
    List all exchanges in a vhost.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.exchange_list
        salt '*' rabbitmq_management.exchange_list /production

    Args:
        vhost: Virtual host name (default: /)

    Returns:
        list: List of dicts with exchange information
    """
    path = f"/api/exchanges/{quote(vhost, safe='')}"
    return _http_request("GET", path, **config_override)


def exchange_get(vhost, name, **config_override):
    """
    Get information about a specific exchange.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.exchange_get / amq.direct
        salt '*' rabbitmq_management.exchange_get /production my-exchange

    Args:
        vhost: Virtual host name
        name: Exchange name

    Returns:
        dict: Exchange details or None if not found
    """
    try:
        path = f"/api/exchanges/{quote(vhost, safe='')}/{quote(name, safe='')}"
        return _http_request("GET", path, **config_override)
    except CommandExecutionError as exc:
        if "404" in str(exc):
            return None
        raise


def exchange_create(
    vhost,
    name,
    type="direct",
    durable=True,
    auto_delete=False,
    internal=False,
    arguments=None,
    **config_override,
):
    """
    Create a new exchange.

    CLI Examples:

    .. code-block:: bash

        # Simple direct exchange
        salt '*' rabbitmq_management.exchange_create / my-exchange

        # Topic exchange
        salt '*' rabbitmq_management.exchange_create / my-topic type=topic

        # Fanout exchange (non-durable)
        salt '*' rabbitmq_management.exchange_create / my-fanout type=fanout durable=False

        # With arguments (alternate exchange)
        salt '*' rabbitmq_management.exchange_create / my-exchange arguments='{"alternate-exchange":"backup-exchange"}'

        # Headers exchange with auto-delete
        salt '*' rabbitmq_management.exchange_create / my-headers type=headers auto_delete=True

    Args:
        vhost: Virtual host name
        name: Exchange name
        type: Exchange type: direct, fanout, topic, headers (default: direct)
        durable: Survive broker restart (default: True)
        auto_delete: Delete when last queue unbinds (default: False)
        internal: Only for exchange-to-exchange bindings (default: False)
        arguments: Additional arguments as dict or JSON string

    Returns:
        dict: Operation result
    """
    data = {
        "type": type,
        "durable": durable,
        "auto_delete": auto_delete,
        "internal": internal,
    }

    if arguments:
        if isinstance(arguments, str):
            arguments = salt.utils.json.loads(arguments)
        data["arguments"] = arguments

    path = f"/api/exchanges/{quote(vhost, safe='')}/{quote(name, safe='')}"
    _http_request("PUT", path, data=data, **config_override)

    return {"status": "created", "vhost": vhost, "name": name, "type": type}


def exchange_delete(vhost, name, if_unused=False, **config_override):
    """
    Delete an exchange.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.exchange_delete / my-exchange

        # Delete only if no queues are bound
        salt '*' rabbitmq_management.exchange_delete / my-exchange if_unused=True

    Args:
        vhost: Virtual host name
        name: Exchange name
        if_unused: Only delete if no queues are bound (default: False)

    Returns:
        dict: Operation result
    """
    path = f"/api/exchanges/{quote(vhost, safe='')}/{quote(name, safe='')}"

    if if_unused:
        path += "?if-unused=true"

    _http_request("DELETE", path, **config_override)

    return {"status": "deleted", "vhost": vhost, "name": name}


def exchange_exist(vhost, name, **config_override):
    """
    Check if an exchange exists.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.exchange_exist / my-exchange

    Args:
        vhost: Virtual host name
        name: Exchange name

    Returns:
        bool: True if exchange exists, False otherwise
    """
    result = exchange_get(vhost, name, **config_override)
    return result is not None


def exchange_bindings_source(vhost, name, **config_override):
    """
    List all bindings where this exchange is the source.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.exchange_bindings_source / my-exchange

    Args:
        vhost: Virtual host name
        name: Exchange name

    Returns:
        list: List of bindings (to queues or other exchanges)
    """
    path = f"/api/exchanges/{quote(vhost, safe='')}/{quote(name, safe='')}/bindings/source"
    return _http_request("GET", path, **config_override)


def exchange_bindings_destination(vhost, name, **config_override):
    """
    List all bindings where this exchange is the destination.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.exchange_bindings_destination / my-exchange

    Args:
        vhost: Virtual host name
        name: Exchange name

    Returns:
        list: List of bindings (from other exchanges)
    """
    path = f"/api/exchanges/{quote(vhost, safe='')}/{quote(name, safe='')}/bindings/destination"
    return _http_request("GET", path, **config_override)


def exchange_publish(
    vhost,
    name,
    routing_key="",
    payload="",
    properties=None,
    payload_encoding="string",
    **config_override,
):
    """
    Publish a message to an exchange (for testing).

    CLI Examples:

    .. code-block:: bash

        # Simple message
        salt '*' rabbitmq_management.exchange_publish / my-exchange routing_key=test payload="Hello World"

        # JSON message
        salt '*' rabbitmq_management.exchange_publish / my-exchange routing_key=orders payload='{"order_id":123}'

        # With properties
        salt '*' rabbitmq_management.exchange_publish / my-exchange routing_key=task \\
            payload="work" properties='{"delivery_mode":2,"priority":5}'

    Args:
        vhost: Virtual host name
        name: Exchange name
        routing_key: Routing key (default: "")
        payload: Message payload (default: "")
        properties: Message properties as dict or JSON string (delivery_mode, headers, etc.)
        payload_encoding: Encoding type: string, base64 (default: string)

    Returns:
        dict: Publish result (routed: true/false)
    """
    data = {
        "routing_key": routing_key,
        "payload": payload,
        "payload_encoding": payload_encoding,
        "properties": properties or {},
    }

    if isinstance(properties, str):
        data["properties"] = salt.utils.json.loads(properties)

    path = f"/api/exchanges/{quote(vhost, safe='')}/{quote(name, safe='')}/publish"
    result = _http_request("POST", path, data=data, **config_override)

    return result
