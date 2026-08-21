"""RabbitMQ federation upstream management via the Management API."""

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_parameter_mod import (
    parameter_create as _parameter_create,
)
from saltext.rabbitmq_management.modules.rabbitmq_management_parameter_mod import (
    parameter_delete as _parameter_delete,
)
from saltext.rabbitmq_management.modules.rabbitmq_management_parameter_mod import (
    parameter_exist as _parameter_exist,
)
from saltext.rabbitmq_management.modules.rabbitmq_management_parameter_mod import (
    parameter_get as _parameter_get,
)
from saltext.rabbitmq_management.modules.rabbitmq_management_parameter_mod import (
    parameter_list as _parameter_list,
)

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


def federation_upstream_create(
    vhost,
    name,
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
    **config_override,
):
    """
    Create a federation upstream (shorthand for parameter_create).

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.federation_upstream_create / my-upstream uri=amqp://server

        salt '*' rabbitmq_management.federation_upstream_create / upstream1 \\
            uri=amqp://remote expires=3600000 prefetch_count=1000

    Args:
        vhost: Virtual host name
        name: Upstream name
        uri: AMQP URI(s) for upstream (can be string or list)
        expires: Queue expiration time in ms
        message_ttl: Message TTL in ms
        max_hops: Maximum hops for messages
        prefetch_count: Prefetch count
        reconnect_delay: Reconnect delay in seconds
        ack_mode: on-confirm, on-publish, no-ack
        trust_user_id: Trust user-id from upstream
        exchange: Upstream exchange name
        queue: Upstream queue name

    Returns:
        dict: Operation result
    """
    value = {"uri": uri}

    if expires is not None:
        value["expires"] = expires
    if message_ttl is not None:
        value["message-ttl"] = message_ttl
    if max_hops is not None:
        value["max-hops"] = max_hops
    if prefetch_count is not None:
        value["prefetch-count"] = prefetch_count
    if reconnect_delay is not None:
        value["reconnect-delay"] = reconnect_delay
    if ack_mode is not None:
        value["ack-mode"] = ack_mode
    if trust_user_id is not None:
        value["trust-user-id"] = trust_user_id
    if exchange is not None:
        value["exchange"] = exchange
    if queue is not None:
        value["queue"] = queue

    return _parameter_create("federation-upstream", vhost, name, value, **config_override)


def federation_upstream_get(vhost, name, **config_override):
    """
    Get a federation upstream parameter.

    :param str vhost: The name of the virtual host.
    :param str name: The name of the federation upstream.
    :param config_override: Optional configuration overrides.
    :return: Federation upstream definition or None if not found.
    :rtype: dict or None

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.federation_upstream_get / my-upstream
        salt '*' rabbitmq_management.federation_upstream_get production remote-dc
    """
    return _parameter_get("federation-upstream", vhost, name, **config_override)


def federation_upstream_list(vhost=None, **config_override):
    """
    List all federation upstream parameters, optionally filtered by vhost.

    :param str vhost: Optional vhost filter.
    :param config_override: Optional configuration overrides.
    :return: List of federation upstreams.
    :rtype: list

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.federation_upstream_list
        salt '*' rabbitmq_management.federation_upstream_list vhost=/
        salt '*' rabbitmq_management.federation_upstream_list vhost=production
    """
    return _parameter_list(component="federation-upstream", vhost=vhost, **config_override)


def federation_upstream_delete(vhost, name, **config_override):
    """
    Delete a federation upstream parameter.

    :param str vhost: The name of the virtual host.
    :param str name: The name of the federation upstream.
    :param config_override: Optional configuration overrides.
    :return: True if successful.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.federation_upstream_delete / my-upstream
        salt '*' rabbitmq_management.federation_upstream_delete production remote-dc
    """
    return _parameter_delete("federation-upstream", vhost, name, **config_override)


def federation_upstream_exist(vhost, name, **config_override):
    """
    Check if a federation upstream parameter exists.

    :param str vhost: The name of the virtual host.
    :param str name: The name of the federation upstream.
    :param config_override: Optional configuration overrides.
    :return: True if exists, False otherwise.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.federation_upstream_exist / my-upstream
        salt '*' rabbitmq_management.federation_upstream_exist production remote-dc
    """
    return _parameter_exist("federation-upstream", vhost, name, **config_override)
