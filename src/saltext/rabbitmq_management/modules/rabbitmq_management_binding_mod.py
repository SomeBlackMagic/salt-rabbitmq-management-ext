"""RabbitMQ binding management via the Management API."""

from urllib.parse import quote

import salt.utils.json

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _http_request

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


# =============================================================================
# Bindings Management (HTTP API)
# =============================================================================


def binding_list(vhost="/", **config_override):
    """
    List all bindings in a vhost.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.binding_list
        salt '*' rabbitmq_management.binding_list /production

    Args:
        vhost: Virtual host name (default: /)

    Returns:
        list: List of all bindings (exchange-to-queue and exchange-to-exchange)
    """
    path = f"/api/bindings/{quote(vhost, safe='')}"
    return _http_request("GET", path, **config_override)


def binding_list_queue(vhost, queue, **config_override):
    """
    List all bindings for a specific queue.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.binding_list_queue / my-queue

    Args:
        vhost: Virtual host name
        queue: Queue name

    Returns:
        list: List of bindings to this queue
    """
    path = f"/api/queues/{quote(vhost, safe='')}/{quote(queue, safe='')}/bindings"
    return _http_request("GET", path, **config_override)


def binding_list_exchange_source(vhost, exchange, **config_override):
    """
    List all bindings where the exchange is the source.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.binding_list_exchange_source / my-exchange

    Args:
        vhost: Virtual host name
        exchange: Exchange name

    Returns:
        list: List of bindings from this exchange
    """
    path = f"/api/exchanges/{quote(vhost, safe='')}/{quote(exchange, safe='')}/bindings/source"
    return _http_request("GET", path, **config_override)


def binding_list_exchange_destination(vhost, exchange, **config_override):
    """
    List all bindings where the exchange is the destination.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.binding_list_exchange_destination / my-exchange

    Args:
        vhost: Virtual host name
        exchange: Exchange name

    Returns:
        list: List of bindings to this exchange
    """
    path = f"/api/exchanges/{quote(vhost, safe='')}/{quote(exchange, safe='')}/bindings/destination"
    return _http_request("GET", path, **config_override)


def binding_create_queue(vhost, exchange, queue, routing_key="", arguments=None, **config_override):
    """
    Create a binding from an exchange to a queue.

    CLI Examples:

    .. code-block:: bash

        # Direct binding
        salt '*' rabbitmq_management.binding_create_queue / my-exchange my-queue routing_key=orders

        # Fanout binding (routing_key ignored)
        salt '*' rabbitmq_management.binding_create_queue / fanout-exchange my-queue

        # Topic binding with wildcard
        salt '*' rabbitmq_management.binding_create_queue / logs my-queue routing_key='app.*.error'

        # Headers binding with arguments
        salt '*' rabbitmq_management.binding_create_queue / headers-ex my-queue \\
            arguments='{"x-match":"all","type":"order","priority":"high"}'

    Args:
        vhost: Virtual host name
        exchange: Source exchange name
        queue: Destination queue name
        routing_key: Routing key pattern (default: "")
        arguments: Binding arguments as dict or JSON string (for headers exchange)

    Returns:
        dict: Operation result
    """
    data = {
        "routing_key": routing_key,
        "arguments": {},
    }

    if arguments:
        if isinstance(arguments, str):
            arguments = salt.utils.json.loads(arguments)
        data["arguments"] = arguments

    path = f"/api/bindings/{quote(vhost, safe='')}/e/{quote(exchange, safe='')}/q/{quote(queue, safe='')}"
    _http_request("POST", path, data=data, **config_override)

    return {
        "status": "created",
        "vhost": vhost,
        "exchange": exchange,
        "queue": queue,
        "routing_key": routing_key,
    }


def binding_create_exchange(
    vhost, source, destination, routing_key="", arguments=None, **config_override
):
    """
    Create a binding from an exchange to another exchange.

    CLI Examples:

    .. code-block:: bash

        # Exchange-to-exchange binding
        salt '*' rabbitmq_management.binding_create_exchange / source-exchange dest-exchange routing_key=process

        # Topic pattern
        salt '*' rabbitmq_management.binding_create_exchange / logs processor routing_key='app.*.error'

    Args:
        vhost: Virtual host name
        source: Source exchange name
        destination: Destination exchange name
        routing_key: Routing key pattern (default: "")
        arguments: Binding arguments as dict or JSON string

    Returns:
        dict: Operation result
    """
    data = {
        "routing_key": routing_key,
        "arguments": {},
    }

    if arguments:
        if isinstance(arguments, str):
            arguments = salt.utils.json.loads(arguments)
        data["arguments"] = arguments

    path = f"/api/bindings/{quote(vhost, safe='')}/e/{quote(source, safe='')}/e/{quote(destination, safe='')}"
    _http_request("POST", path, data=data, **config_override)

    return {
        "status": "created",
        "vhost": vhost,
        "source": source,
        "destination": destination,
        "routing_key": routing_key,
    }


def binding_delete_queue(vhost, exchange, queue, properties_key, **config_override):
    """
    Delete a binding from an exchange to a queue.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.binding_delete_queue / my-exchange my-queue orders

    Args:
        vhost: Virtual host name
        exchange: Source exchange name
        queue: Destination queue name
        properties_key: Binding properties key (routing_key or special identifier)

    Returns:
        dict: Operation result

    Note:
        The properties_key is typically the routing_key used when creating the binding,
        or a special identifier returned by RabbitMQ for bindings with arguments.
        Use binding_list_queue to find the exact properties_key.
    """
    path = f"/api/bindings/{quote(vhost, safe='')}/e/{quote(exchange, safe='')}/q/{quote(queue, safe='')}/{quote(properties_key, safe='')}"
    _http_request("DELETE", path, **config_override)

    return {
        "status": "deleted",
        "vhost": vhost,
        "exchange": exchange,
        "queue": queue,
        "properties_key": properties_key,
    }


def binding_delete_exchange(vhost, source, destination, properties_key, **config_override):
    """
    Delete a binding from an exchange to another exchange.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.binding_delete_exchange / source-exchange dest-exchange process

    Args:
        vhost: Virtual host name
        source: Source exchange name
        destination: Destination exchange name
        properties_key: Binding properties key (routing_key or special identifier)

    Returns:
        dict: Operation result

    Note:
        Use binding_list_exchange_source to find the exact properties_key.
    """
    path = f"/api/bindings/{quote(vhost, safe='')}/e/{quote(source, safe='')}/e/{quote(destination, safe='')}/{quote(properties_key, safe='')}"
    _http_request("DELETE", path, **config_override)

    return {
        "status": "deleted",
        "vhost": vhost,
        "source": source,
        "destination": destination,
        "properties_key": properties_key,
    }
