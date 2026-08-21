"""Salt states for managing RabbitMQ federation upstreams."""

import logging

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"

_REQUIRED_FUNCTIONS = (
    "rabbitmq_management.federation_upstream_create",
    "rabbitmq_management.federation_upstream_delete",
    "rabbitmq_management.federation_upstream_exist",
    "rabbitmq_management.federation_upstream_get",
)

_PARAM_TO_VALUE_KEY = {
    "uri": "uri",
    "expires": "expires",
    "message_ttl": "message-ttl",
    "max_hops": "max-hops",
    "prefetch_count": "prefetch-count",
    "reconnect_delay": "reconnect-delay",
    "ack_mode": "ack-mode",
    "trust_user_id": "trust-user-id",
    "exchange": "exchange",
    "queue": "queue",
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
    uri,
    expires,
    message_ttl,
    max_hops,
    prefetch_count,
    reconnect_delay,
    ack_mode,
    trust_user_id,
    exchange,
    queue,
):
    """Build the desired upstream value dict using API key names."""
    params = {
        "uri": uri,
        "expires": expires,
        "message_ttl": message_ttl,
        "max_hops": max_hops,
        "prefetch_count": prefetch_count,
        "reconnect_delay": reconnect_delay,
        "ack_mode": ack_mode,
        "trust_user_id": trust_user_id,
        "exchange": exchange,
        "queue": queue,
    }
    value = {}
    for param, api_key in _PARAM_TO_VALUE_KEY.items():
        v = params[param]
        if v is not None:
            value[api_key] = v
    return value


def federation_upstream_present(
    name,
    vhost,
    uri,
    expires=None,
    message_ttl=None,
    max_hops=None,
    prefetch_count=None,
    reconnect_delay=None,
    ack_mode=None,
    trust_user_id=None,
    exchange=None,
    queue=None,
    **connection_args,
):
    """
    Ensure a RabbitMQ federation upstream exists with the desired configuration.

    When the upstream exists but its ``value`` differs from the desired configuration,
    the upstream is updated via a PUT call to the Management API.

    Args:
        name: Upstream name
        vhost: Virtual host name
        uri: AMQP URI(s) for the remote server (string or list)
        expires: Queue expiration time in milliseconds
        message_ttl: Message TTL in milliseconds
        max_hops: Maximum number of hops for messages
        prefetch_count: Prefetch count
        reconnect_delay: Reconnect delay in seconds
        ack_mode: Acknowledgement mode: on-confirm, on-publish, no-ack
        trust_user_id: Trust user-id from the upstream
        exchange: Upstream exchange name
        queue: Upstream queue name
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        remote_dc_upstream:
          rabbitmq_management.federation_upstream_present:
            - name: remote-dc
            - vhost: /
            - uri: amqp://rabbit@remote-dc.internal
            - expires: 3600000
            - prefetch_count: 1000
            - ack_mode: on-confirm

        ha_upstream:
          rabbitmq_management.federation_upstream_present:
            - name: ha-upstream
            - vhost: /production
            - uri:
              - amqp://node1.rabbit.internal
              - amqp://node2.rabbit.internal
            - reconnect_delay: 5
    """
    ret = _state_return(name)

    desired_value = _build_desired_value(
        uri,
        expires,
        message_ttl,
        max_hops,
        prefetch_count,
        reconnect_delay,
        ack_mode,
        trust_user_id,
        exchange,
        queue,
    )

    try:
        current = __salt__["rabbitmq_management.federation_upstream_get"](
            vhost, name, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to get federation upstream %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to get federation upstream '{name}': {err}"
        return ret

    if current is None:
        ret["changes"] = {
            "old": None,
            "new": {"vhost": vhost, "name": name, "value": desired_value},
        }
        if __opts__.get("test", False):
            ret["result"] = None
            ret["comment"] = f"Federation upstream '{name}' would be created"
            return ret
        try:
            __salt__["rabbitmq_management.federation_upstream_create"](
                vhost,
                name,
                uri=uri,
                expires=expires,
                message_ttl=message_ttl,
                max_hops=max_hops,
                prefetch_count=prefetch_count,
                reconnect_delay=reconnect_delay,
                ack_mode=ack_mode,
                trust_user_id=trust_user_id,
                exchange=exchange,
                queue=queue,
                **connection_args,
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            log.exception("Failed to create federation upstream %s", name)
            ret["result"] = False
            ret["changes"] = {}
            ret["comment"] = f"Failed to create federation upstream '{name}': {err}"
            return ret
        ret["comment"] = f"Federation upstream '{name}' created"
        return ret

    current_value = current.get("value", {})
    if current_value == desired_value:
        ret["comment"] = f"Federation upstream '{name}' is already in the desired state"
        return ret

    ret["changes"] = {
        "old": {"value": current_value},
        "new": {"value": desired_value},
    }
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Federation upstream '{name}' would be updated"
        return ret

    try:
        __salt__["rabbitmq_management.federation_upstream_create"](
            vhost,
            name,
            uri=uri,
            expires=expires,
            message_ttl=message_ttl,
            max_hops=max_hops,
            prefetch_count=prefetch_count,
            reconnect_delay=reconnect_delay,
            ack_mode=ack_mode,
            trust_user_id=trust_user_id,
            exchange=exchange,
            queue=queue,
            **connection_args,
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to update federation upstream %s", name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to update federation upstream '{name}': {err}"
        return ret

    ret["comment"] = f"Federation upstream '{name}' updated"
    return ret


def federation_upstream_absent(name, vhost, **connection_args):
    """
    Ensure a RabbitMQ federation upstream does not exist.

    Args:
        name: Upstream name
        vhost: Virtual host name
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        remove_old_upstream:
          rabbitmq_management.federation_upstream_absent:
            - name: legacy-dc
            - vhost: /
    """
    ret = _state_return(name)

    try:
        exists = __salt__["rabbitmq_management.federation_upstream_exist"](
            vhost, name, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to check federation upstream %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to check federation upstream '{name}': {err}"
        return ret

    if not exists:
        ret["comment"] = f"Federation upstream '{name}' on vhost '{vhost}' is already absent"
        return ret

    ret["changes"] = {"old": name, "new": None}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Federation upstream '{name}' would be removed"
        return ret

    try:
        __salt__["rabbitmq_management.federation_upstream_delete"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove federation upstream %s", name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to remove federation upstream '{name}': {err}"
        return ret

    ret["comment"] = f"Federation upstream '{name}' removed"
    return ret
