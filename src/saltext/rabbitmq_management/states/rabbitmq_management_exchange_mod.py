"""Salt states for managing RabbitMQ exchanges."""

import logging

import salt.utils.json

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"

_REQUIRED_FUNCTIONS = (
    "rabbitmq_management.exchange_create",
    "rabbitmq_management.exchange_delete",
    "rabbitmq_management.exchange_exist",
    "rabbitmq_management.exchange_get",
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
    """Normalize exchange arguments to a dictionary."""
    if arguments is None:
        return {}
    if isinstance(arguments, str):
        arguments = salt.utils.json.loads(arguments)
    if not isinstance(arguments, dict):
        raise TypeError("arguments must be a dictionary or a JSON object")
    return arguments


def _is_builtin(name):
    """Return True when the exchange name is a RabbitMQ built-in (amq.*)."""
    return name.startswith("amq.")


def _params_differ(current, type, durable, auto_delete, internal, arguments):
    """Return True when the current exchange parameters differ from the desired ones."""
    return (
        current.get("type") != type
        or current.get("durable") != durable
        or current.get("auto_delete") != auto_delete
        or current.get("internal") != internal
        or _normalize_arguments(current.get("arguments")) != arguments
    )


def _changed_fields(current, type, durable, auto_delete, internal, arguments):
    """Return only the fields that differ between current and desired state."""
    old = {}
    new = {}
    if current.get("type") != type:
        old["type"] = current.get("type")
        new["type"] = type
    if current.get("durable") != durable:
        old["durable"] = current.get("durable")
        new["durable"] = durable
    if current.get("auto_delete") != auto_delete:
        old["auto_delete"] = current.get("auto_delete")
        new["auto_delete"] = auto_delete
    if current.get("internal") != internal:
        old["internal"] = current.get("internal")
        new["internal"] = internal
    current_arguments = _normalize_arguments(current.get("arguments"))
    if current_arguments != arguments:
        old["arguments"] = current_arguments
        new["arguments"] = arguments
    return {"old": old, "new": new}


def exchange_present(
    name,
    vhost="/",
    type="direct",
    durable=True,
    auto_delete=False,
    internal=False,
    arguments=None,
    force=False,
    **connection_args,
):
    """
    Ensure a RabbitMQ exchange exists with the desired configuration.

    RabbitMQ does not allow modifying ``type``, ``durable``, ``auto_delete``, or
    ``internal`` on an existing exchange. When these parameters differ from the
    current exchange configuration the state fails by default. Set ``force=True``
    to delete and recreate the exchange.

    Built-in exchanges (names starting with ``amq.``) cannot be deleted or
    recreated. The state will fail if a conflict is detected on a built-in exchange.

    Args:
        name: Exchange name
        vhost: Virtual host (default: ``/``)
        type: Exchange type: direct, fanout, topic, headers (default: ``direct``)
        durable: Survive broker restart (default: ``True``)
        auto_delete: Delete when last queue unbinds (default: ``False``)
        internal: Only for exchange-to-exchange bindings (default: ``False``)
        arguments: Exchange arguments as a dictionary or JSON string
        force: Delete and recreate the exchange when parameters conflict
            (default: ``False``)
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        orders_exchange:
          rabbitmq_management.exchange_present:
            - name: orders
            - vhost: /production
            - type: topic
            - durable: true
    """
    ret = _state_return(name)

    try:
        normalized_arguments = _normalize_arguments(arguments)
    except (TypeError, ValueError) as err:
        ret["result"] = False
        ret["comment"] = f"Invalid exchange arguments: {err}"
        return ret

    try:
        current = __salt__["rabbitmq_management.exchange_get"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to get RabbitMQ exchange %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to get exchange '{name}': {err}"
        return ret

    desired = {
        "vhost": vhost,
        "name": name,
        "type": type,
        "durable": durable,
        "auto_delete": auto_delete,
        "internal": internal,
        "arguments": normalized_arguments,
    }

    if current is None:
        ret["changes"] = {"old": None, "new": desired}
        if __opts__.get("test", False):
            ret["result"] = None
            ret["comment"] = f"Exchange '{name}' would be created"
            return ret
        try:
            __salt__["rabbitmq_management.exchange_create"](
                vhost,
                name,
                type=type,
                durable=durable,
                auto_delete=auto_delete,
                internal=internal,
                arguments=normalized_arguments,
                **connection_args,
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            log.exception("Failed to create RabbitMQ exchange %s", name)
            ret["result"] = False
            ret["changes"] = {}
            ret["comment"] = f"Failed to create exchange '{name}': {err}"
            return ret
        ret["comment"] = f"Exchange '{name}' created"
        return ret

    if not _params_differ(current, type, durable, auto_delete, internal, normalized_arguments):
        ret["comment"] = f"Exchange '{name}' is already in the desired state"
        return ret

    if _is_builtin(name):
        ret["result"] = False
        ret["comment"] = (
            f"Exchange '{name}' is a built-in RabbitMQ exchange (amq.*) and cannot be recreated."
        )
        return ret

    if not force:
        ret["result"] = False
        ret["comment"] = (
            f"Exchange '{name}' exists with different parameters. Use force=True to recreate it."
        )
        return ret

    ret["changes"] = _changed_fields(
        current, type, durable, auto_delete, internal, normalized_arguments
    )
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Exchange '{name}' would be recreated"
        return ret

    try:
        __salt__["rabbitmq_management.exchange_delete"](vhost, name, **connection_args)
        __salt__["rabbitmq_management.exchange_create"](
            vhost,
            name,
            type=type,
            durable=durable,
            auto_delete=auto_delete,
            internal=internal,
            arguments=normalized_arguments,
            **connection_args,
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to recreate RabbitMQ exchange %s", name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to recreate exchange '{name}': {err}"
        return ret

    ret["comment"] = f"Exchange '{name}' recreated"
    return ret


def exchange_absent(name, vhost="/", if_unused=False, **connection_args):
    """
    Ensure a RabbitMQ exchange does not exist.

    Built-in exchanges (names starting with ``amq.``) cannot be deleted.
    The state will fail if removal of a built-in exchange is requested.

    Args:
        name: Exchange name
        vhost: Virtual host (default: ``/``)
        if_unused: Only delete the exchange if no queues are bound (default: ``False``)
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        remove_old_exchange:
          rabbitmq_management.exchange_absent:
            - name: legacy-fanout
            - vhost: /
            - if_unused: true
    """
    ret = _state_return(name)

    if _is_builtin(name):
        ret["result"] = False
        ret["comment"] = (
            f"Exchange '{name}' is a built-in RabbitMQ exchange (amq.*) and cannot be removed."
        )
        return ret

    try:
        exists = __salt__["rabbitmq_management.exchange_exist"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to check RabbitMQ exchange %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to check exchange '{name}': {err}"
        return ret

    if not exists:
        ret["comment"] = f"Exchange '{name}' on vhost '{vhost}' is already absent"
        return ret

    ret["changes"] = {"old": name, "new": None}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Exchange '{name}' would be removed"
        return ret

    try:
        __salt__["rabbitmq_management.exchange_delete"](
            vhost, name, if_unused=if_unused, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove RabbitMQ exchange %s", name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to remove exchange '{name}': {err}"
        return ret

    ret["comment"] = f"Exchange '{name}' removed"
    return ret
