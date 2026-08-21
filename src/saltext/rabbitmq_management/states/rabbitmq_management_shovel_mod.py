"""
Salt states for managing RabbitMQ shovels.

Shovels move messages from a source queue on one broker to a destination queue
on another (or the same) broker. They are configured as runtime parameters
under the ``shovel`` component via the RabbitMQ Management API.

States
------

* :py:func:`shovel_present` — ensure a shovel exists with the desired configuration.
* :py:func:`shovel_absent` — ensure a shovel does not exist.
"""

import logging

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"

_REQUIRED_FUNCTIONS = (
    "rabbitmq_management.shovel_create",
    "rabbitmq_management.shovel_delete",
    "rabbitmq_management.shovel_exist",
    "rabbitmq_management.shovel_get",
)

_PARAM_TO_VALUE_KEY = {
    "src_uri": "src-uri",
    "src_queue": "src-queue",
    "dest_uri": "dest-uri",
    "dest_queue": "dest-queue",
    "prefetch_count": "prefetch-count",
    "reconnect_delay": "reconnect-delay",
    "ack_mode": "ack-mode",
    "src_delete_after": "src-delete-after",
}


def __virtual__():
    """Load only when all required RabbitMQ execution functions are available."""
    missing = [f for f in _REQUIRED_FUNCTIONS if f not in __salt__]
    if missing:
        return False, "Required execution functions are not available: {}".format(
            ", ".join(missing)
        )
    return __virtualname__


def _state_return(name):
    return {"name": name, "result": True, "changes": {}, "comment": ""}


def _build_desired_value(
    src_uri,
    src_queue,
    dest_uri,
    dest_queue,
    prefetch_count,
    reconnect_delay,
    ack_mode,
    src_delete_after,
):
    """Build the desired shovel value dict using API key names."""
    params = {
        "src_uri": src_uri,
        "src_queue": src_queue,
        "dest_uri": dest_uri,
        "dest_queue": dest_queue,
        "prefetch_count": prefetch_count,
        "reconnect_delay": reconnect_delay,
        "ack_mode": ack_mode,
        "src_delete_after": src_delete_after,
    }
    value = {}
    for param, api_key in _PARAM_TO_VALUE_KEY.items():
        v = params[param]
        if v is not None:
            value[api_key] = v
    return value


def shovel_present(
    name,
    vhost,
    src_uri,
    src_queue,
    dest_uri,
    dest_queue,
    prefetch_count=None,
    reconnect_delay=None,
    ack_mode=None,
    src_delete_after=None,
    **connection_args,
):
    """
    Ensure a RabbitMQ shovel exists with the desired configuration.

    When the shovel exists but its ``value`` differs from the desired configuration,
    the shovel is updated via a PUT call to the Management API.

    This state is idempotent: repeated calls with the same arguments produce no
    changes once the shovel reaches the desired state.

    Args:
        name: Shovel name.
        vhost: Virtual host name.
        src_uri: AMQP URI of the source broker (e.g. ``amqp://user:pass@host/vhost``).
        src_queue: Name of the source queue.
        dest_uri: AMQP URI of the destination broker.
        dest_queue: Name of the destination queue.
        prefetch_count: Maximum number of unacknowledged messages in flight.
        reconnect_delay: Seconds to wait before reconnecting after a failure.
        ack_mode: Acknowledgement mode. One of ``on-confirm`` (default RabbitMQ
            behaviour), ``on-publish``, or ``no-ack``.
        src_delete_after: When to delete messages from the source. Either
            ``never`` (keep source messages) or ``queue-length`` (delete after
            moving the number of messages present at shovel startup).
        **connection_args: Optional connection parameter overrides passed to
            every underlying execution-module call.

    Returns:
        Standard Salt state dict with ``result``, ``changes``, and ``comment``.
        ``changes`` is empty when the shovel is already in the desired state.

    Example:

    .. code-block:: yaml

        migrate_orders:
          rabbitmq_management.shovel_present:
            - name: orders-migration
            - vhost: /
            - src_uri: amqp://old-cluster
            - src_queue: orders
            - dest_uri: amqp://new-cluster
            - dest_queue: orders
            - ack_mode: on-confirm
            - prefetch_count: 500

        cleanup_shovel:
          rabbitmq_management.shovel_present:
            - name: drain-temp
            - vhost: /staging
            - src_uri: amqp://
            - src_queue: temp-queue
            - dest_uri: amqp://
            - dest_queue: archive-queue
            - src_delete_after: queue-length
    """
    ret = _state_return(name)

    desired_value = _build_desired_value(
        src_uri,
        src_queue,
        dest_uri,
        dest_queue,
        prefetch_count,
        reconnect_delay,
        ack_mode,
        src_delete_after,
    )

    try:
        current = __salt__["rabbitmq_management.shovel_get"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to get shovel %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to get shovel '{name}': {err}"
        return ret

    if current is None:
        ret["changes"] = {
            "old": None,
            "new": {"vhost": vhost, "name": name, "value": desired_value},
        }
        if __opts__.get("test", False):
            ret["result"] = None
            ret["comment"] = f"Shovel '{name}' would be created"
            return ret
        try:
            __salt__["rabbitmq_management.shovel_create"](
                vhost,
                name,
                src_uri=src_uri,
                src_queue=src_queue,
                dest_uri=dest_uri,
                dest_queue=dest_queue,
                prefetch_count=prefetch_count,
                reconnect_delay=reconnect_delay,
                ack_mode=ack_mode,
                src_delete_after=src_delete_after,
                **connection_args,
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            log.exception("Failed to create shovel %s", name)
            ret["result"] = False
            ret["changes"] = {}
            ret["comment"] = f"Failed to create shovel '{name}': {err}"
            return ret
        ret["comment"] = f"Shovel '{name}' created"
        return ret

    current_value = current.get("value", {})
    if current_value == desired_value:
        ret["comment"] = f"Shovel '{name}' is already in the desired state"
        return ret

    ret["changes"] = {
        "old": {"value": current_value},
        "new": {"value": desired_value},
    }
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Shovel '{name}' would be updated"
        return ret

    try:
        __salt__["rabbitmq_management.shovel_create"](
            vhost,
            name,
            src_uri=src_uri,
            src_queue=src_queue,
            dest_uri=dest_uri,
            dest_queue=dest_queue,
            prefetch_count=prefetch_count,
            reconnect_delay=reconnect_delay,
            ack_mode=ack_mode,
            src_delete_after=src_delete_after,
            **connection_args,
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to update shovel %s", name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to update shovel '{name}': {err}"
        return ret

    ret["comment"] = f"Shovel '{name}' updated"
    return ret


def shovel_absent(name, vhost, **connection_args):
    """
    Ensure a RabbitMQ shovel does not exist.

    If the shovel is already absent the state succeeds without changes.

    Args:
        name: Shovel name.
        vhost: Virtual host name.
        **connection_args: Optional connection parameter overrides passed to
            every underlying execution-module call.

    Returns:
        Standard Salt state dict with ``result``, ``changes``, and ``comment``.
        ``changes`` is empty when the shovel was already absent.

    Example:

    .. code-block:: yaml

        stop_migration_shovel:
          rabbitmq_management.shovel_absent:
            - name: orders-migration
            - vhost: /
    """
    ret = _state_return(name)

    try:
        exists = __salt__["rabbitmq_management.shovel_exist"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to check shovel %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to check shovel '{name}': {err}"
        return ret

    if not exists:
        ret["comment"] = f"Shovel '{name}' on vhost '{vhost}' is already absent"
        return ret

    ret["changes"] = {"old": name, "new": None}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Shovel '{name}' would be removed"
        return ret

    try:
        __salt__["rabbitmq_management.shovel_delete"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove shovel %s", name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to remove shovel '{name}': {err}"
        return ret

    ret["comment"] = f"Shovel '{name}' removed"
    return ret
