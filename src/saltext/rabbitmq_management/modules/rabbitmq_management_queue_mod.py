"""RabbitMQ queue management via the Management API."""

from urllib.parse import quote

import salt.utils.json
from salt.exceptions import CommandExecutionError

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _http_request

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


# =============================================================================
# Queues Management (HTTP API)
# =============================================================================


def queue_list(vhost="/", **config_override):
    """
    List all queues in a vhost.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.queue_list
        salt '*' rabbitmq_management.queue_list /production

    Args:
        vhost: Virtual host name (default: /)

    Returns:
        list: List of dicts with queue information
    """
    path = f"/api/queues/{quote(vhost, safe='')}"
    return _http_request("GET", path, **config_override)


def queue_get(vhost, name, **config_override):
    """
    Get information about a specific queue.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.queue_get / myqueue
        salt '*' rabbitmq_management.queue_get /production orders-queue

    Args:
        vhost: Virtual host name
        name: Queue name

    Returns:
        dict: Queue details or None if not found
    """
    try:
        path = f"/api/queues/{quote(vhost, safe='')}/{quote(name, safe='')}"
        return _http_request("GET", path, **config_override)
    except CommandExecutionError as exc:
        if "404" in str(exc):
            return None
        raise


def queue_create(vhost, name, durable=True, auto_delete=False, arguments=None, **config_override):
    """
    Create a new queue.

    CLI Examples:

    .. code-block:: bash

        # Simple classic queue
        salt '*' rabbitmq_management.queue_create / my-queue

        # Quorum queue (HA)
        salt '*' rabbitmq_management.queue_create / my-queue arguments='{"x-queue-type":"quorum"}'

        # Stream queue
        salt '*' rabbitmq_management.queue_create / my-stream arguments='{"x-queue-type":"stream"}'

        # With message TTL
        salt '*' rabbitmq_management.queue_create / ttl-queue arguments='{"x-message-ttl":60000}'

        # With max length
        salt '*' rabbitmq_management.queue_create / limited arguments='{"x-max-length":1000}'

        # Auto-delete queue
        salt '*' rabbitmq_management.queue_create / temp-queue auto_delete=True

        # Non-durable queue
        salt '*' rabbitmq_management.queue_create / temp durable=False

    Args:
        vhost: Virtual host name
        name: Queue name
        durable: Survive broker restart (default: True)
        auto_delete: Delete when last consumer disconnects (default: False)
        arguments: Additional arguments as dict or JSON string:
            - x-message-ttl: Message TTL in milliseconds
            - x-expires: Queue expiration time in milliseconds
            - x-max-length: Maximum queue length
            - x-max-length-bytes: Maximum queue size in bytes
            - x-overflow: Queue overflow behavior (drop-head, reject-publish, reject-publish-dlx)
            - x-dead-letter-exchange: Dead letter exchange
            - x-dead-letter-routing-key: Routing key for dead letters
            - x-max-priority: Maximum message priority (1-255)
            - x-queue-type: classic, quorum, stream

    Returns:
        dict: Operation result
    """
    data = {
        "durable": durable,
        "auto_delete": auto_delete,
        "arguments": {},
    }

    # Handle queue-specific arguments
    if arguments:
        if isinstance(arguments, str):
            arguments = salt.utils.json.loads(arguments)
        data["arguments"] = arguments

    path = f"/api/queues/{quote(vhost, safe='')}/{quote(name, safe='')}"
    _http_request("PUT", path, data=data, **config_override)

    return {"status": "created", "vhost": vhost, "name": name}


def queue_delete(vhost, name, if_empty=False, if_unused=False, **config_override):
    """
    Delete a queue.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.queue_delete / my-queue

        # Delete only if empty
        salt '*' rabbitmq_management.queue_delete / my-queue if_empty=True

        # Delete only if no consumers
        salt '*' rabbitmq_management.queue_delete / my-queue if_unused=True

    Args:
        vhost: Virtual host name
        name: Queue name
        if_empty: Only delete if queue is empty (default: False)
        if_unused: Only delete if no consumers (default: False)

    Returns:
        dict: Operation result
    """
    path = f"/api/queues/{quote(vhost, safe='')}/{quote(name, safe='')}"

    params = []
    if if_empty:
        params.append("if-empty=true")
    if if_unused:
        params.append("if-unused=true")

    if params:
        path += "?" + "&".join(params)

    _http_request("DELETE", path, **config_override)

    return {"status": "deleted", "vhost": vhost, "name": name}


def queue_exist(vhost, name, **config_override):
    """
    Check if a queue exists.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.queue_exist / my-queue

    Args:
        vhost: Virtual host name
        name: Queue name

    Returns:
        bool: True if queue exists, False otherwise
    """
    try:
        result = queue_get(vhost, name, **config_override)
        return result is not None
    except CommandExecutionError:
        return False


def queue_purge(vhost, name, **config_override):
    """
    Purge all messages from a queue.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.queue_purge / my-queue

    Args:
        vhost: Virtual host name
        name: Queue name

    Returns:
        dict: Operation result
    """
    path = f"/api/queues/{quote(vhost, safe='')}/{quote(name, safe='')}/contents"
    _http_request("DELETE", path, **config_override)

    return {"status": "purged", "vhost": vhost, "name": name}


def queue_get_messages(
    vhost, name, count=1, ack_mode="ack_requeue_true", encoding="auto", **config_override
):
    """
    Get messages from a queue (for inspection/testing).

    CLI Examples:

    .. code-block:: bash

        # Get one message (requeue it)
        salt '*' rabbitmq_management.queue_get_messages / my-queue

        # Get 10 messages
        salt '*' rabbitmq_management.queue_get_messages / my-queue count=10

        # Get and acknowledge (remove from queue)
        salt '*' rabbitmq_management.queue_get_messages / my-queue ack_mode=ack_requeue_false

        # Get without acknowledging
        salt '*' rabbitmq_management.queue_get_messages / my-queue ack_mode=reject_requeue_true

    Args:
        vhost: Virtual host name
        name: Queue name
        count: Number of messages to get (default: 1)
        ack_mode: Acknowledgement mode:
                  - ack_requeue_true: Get and requeue (default)
                  - ack_requeue_false: Get and remove from queue
                  - reject_requeue_true: Get but don't ack
                  - reject_requeue_false: Get and reject
        encoding: Payload encoding: auto, base64 (default: auto)

    Returns:
        list: List of messages with properties and payload
    """
    data = {
        "count": count,
        "ack_mode": ack_mode,
        "encoding": encoding,
    }

    path = f"/api/queues/{quote(vhost, safe='')}/{quote(name, safe='')}/get"
    result = _http_request("POST", path, data=data, **config_override)

    return result


def queue_bindings(vhost, name, **config_override):
    """
    List all bindings for a queue.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.queue_bindings / my-queue

    Args:
        vhost: Virtual host name
        name: Queue name

    Returns:
        list: List of bindings (from exchanges)
    """
    path = f"/api/queues/{quote(vhost, safe='')}/{quote(name, safe='')}/bindings"
    return _http_request("GET", path, **config_override)
