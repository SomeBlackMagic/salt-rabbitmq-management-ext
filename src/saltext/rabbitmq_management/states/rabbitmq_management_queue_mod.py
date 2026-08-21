"""Salt states for managing RabbitMQ queues."""

import logging

import salt.utils.json

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"

_REQUIRED_FUNCTIONS = (
    "rabbitmq_management.queue_create",
    "rabbitmq_management.queue_delete",
    "rabbitmq_management.queue_exist",
    "rabbitmq_management.queue_get",
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
    """Normalize queue arguments to a dictionary."""
    if arguments is None:
        return {}
    if isinstance(arguments, str):
        arguments = salt.utils.json.loads(arguments)
    if not isinstance(arguments, dict):
        raise TypeError("arguments must be a dictionary or a JSON object")
    return arguments


def _params_differ(current, durable, auto_delete, arguments):
    """Return True when the current queue parameters differ from the desired ones."""
    return (
        current.get("durable") != durable
        or current.get("auto_delete") != auto_delete
        or _normalize_arguments(current.get("arguments")) != arguments
    )


def _changed_fields(current, durable, auto_delete, arguments):
    """Return only the fields that differ between current and desired state."""
    old = {}
    new = {}
    if current.get("durable") != durable:
        old["durable"] = current.get("durable")
        new["durable"] = durable
    if current.get("auto_delete") != auto_delete:
        old["auto_delete"] = current.get("auto_delete")
        new["auto_delete"] = auto_delete
    current_arguments = _normalize_arguments(current.get("arguments"))
    if current_arguments != arguments:
        old["arguments"] = current_arguments
        new["arguments"] = arguments
    return {"old": old, "new": new}


def queue_present(
    name,
    vhost="/",
    durable=True,
    auto_delete=False,
    arguments=None,
    force=False,
    **connection_args,
):
    """
    Ensure a RabbitMQ queue exists with the desired configuration.

    RabbitMQ does not allow modifying ``durable``, ``auto_delete``, or
    ``arguments`` on an existing queue. When these parameters differ from the
    current queue configuration the state fails by default. Set ``force=True``
    to delete and recreate the queue. This is a destructive operation that
    discards all messages in the queue.

    Args:
        name: Queue name
        vhost: Virtual host (default: ``/``)
        durable: Survive broker restart (default: ``True``)
        auto_delete: Delete when last consumer disconnects (default: ``False``)
        arguments: Queue arguments as a dictionary or JSON string (e.g.
            ``x-queue-type``, ``x-message-ttl``, ``x-max-length``)
        force: Delete and recreate the queue when parameters conflict
            (default: ``False``)
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        orders_queue:
          rabbitmq_management.queue_present:
            - name: orders
            - vhost: /production
            - durable: true
            - arguments:
                x-queue-type: quorum
                x-message-ttl: 86400000
    """
    ret = _state_return(name)

    try:
        normalized_arguments = _normalize_arguments(arguments)
    except (TypeError, ValueError) as err:
        ret["result"] = False
        ret["comment"] = f"Invalid queue arguments: {err}"
        return ret

    try:
        current = __salt__["rabbitmq_management.queue_get"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to get RabbitMQ queue %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to get queue '{name}': {err}"
        return ret

    desired = {
        "vhost": vhost,
        "name": name,
        "durable": durable,
        "auto_delete": auto_delete,
        "arguments": normalized_arguments,
    }

    if current is None:
        ret["changes"] = {"old": None, "new": desired}
        if __opts__.get("test", False):
            ret["result"] = None
            ret["comment"] = f"Queue '{name}' would be created"
            return ret
        try:
            __salt__["rabbitmq_management.queue_create"](
                vhost, name, durable, auto_delete, normalized_arguments, **connection_args
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            log.exception("Failed to create RabbitMQ queue %s", name)
            ret["result"] = False
            ret["changes"] = {}
            ret["comment"] = f"Failed to create queue '{name}': {err}"
            return ret
        ret["comment"] = f"Queue '{name}' created"
        return ret

    if not _params_differ(current, durable, auto_delete, normalized_arguments):
        ret["comment"] = f"Queue '{name}' is already in the desired state"
        return ret

    if not force:
        ret["result"] = False
        ret["comment"] = (
            f"Queue '{name}' exists with different parameters. Use force=True to recreate it."
        )
        return ret

    ret["changes"] = _changed_fields(current, durable, auto_delete, normalized_arguments)
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Queue '{name}' would be recreated"
        return ret

    try:
        __salt__["rabbitmq_management.queue_delete"](vhost, name, **connection_args)
        __salt__["rabbitmq_management.queue_create"](
            vhost, name, durable, auto_delete, normalized_arguments, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to recreate RabbitMQ queue %s", name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to recreate queue '{name}': {err}"
        return ret

    ret["comment"] = f"Queue '{name}' recreated"
    return ret


def queue_absent(name, vhost="/", if_empty=False, if_unused=False, **connection_args):
    """
    Ensure a RabbitMQ queue does not exist.

    Args:
        name: Queue name
        vhost: Virtual host (default: ``/``)
        if_empty: Only delete the queue if it is empty (default: ``False``)
        if_unused: Only delete the queue if it has no consumers (default: ``False``)
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        remove_temp_queue:
          rabbitmq_management.queue_absent:
            - name: temp-processing
            - vhost: /
            - if_empty: true
    """
    ret = _state_return(name)

    try:
        exists = __salt__["rabbitmq_management.queue_exist"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to check RabbitMQ queue %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to check queue '{name}': {err}"
        return ret

    if not exists:
        ret["comment"] = f"Queue '{name}' on vhost '{vhost}' is already absent"
        return ret

    ret["changes"] = {"old": name, "new": None}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Queue '{name}' would be removed"
        return ret

    try:
        __salt__["rabbitmq_management.queue_delete"](
            vhost, name, if_empty=if_empty, if_unused=if_unused, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove RabbitMQ queue %s", name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to remove queue '{name}': {err}"
        return ret

    ret["comment"] = f"Queue '{name}' removed"
    return ret
