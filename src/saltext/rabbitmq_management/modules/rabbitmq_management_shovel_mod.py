"""RabbitMQ shovel management via the Management API."""

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


def shovel_create(
    vhost,
    name,
    src_uri,
    src_queue,
    dest_uri,
    dest_queue,
    prefetch_count=None,
    reconnect_delay=None,
    ack_mode=None,
    src_delete_after=None,
    **config_override,
):
    """
    Create a shovel (shorthand for parameter_create).

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.shovel_create / my-shovel \\
            src_uri=amqp://source src_queue=source-q \\
            dest_uri=amqp://dest dest_queue=dest-q

    Args:
        vhost: Virtual host name
        name: Shovel name
        src_uri: Source AMQP URI
        src_queue: Source queue name
        dest_uri: Destination AMQP URI
        dest_queue: Destination queue name
        prefetch_count: Prefetch count
        reconnect_delay: Reconnect delay in seconds
        ack_mode: on-confirm, on-publish, no-ack
        src_delete_after: Delete source after (never, queue-length)

    Returns:
        dict: Operation result
    """
    value = {
        "src-uri": src_uri,
        "src-queue": src_queue,
        "dest-uri": dest_uri,
        "dest-queue": dest_queue,
    }

    if prefetch_count is not None:
        value["prefetch-count"] = prefetch_count
    if reconnect_delay is not None:
        value["reconnect-delay"] = reconnect_delay
    if ack_mode is not None:
        value["ack-mode"] = ack_mode
    if src_delete_after is not None:
        value["src-delete-after"] = src_delete_after

    return _parameter_create("shovel", vhost, name, value, **config_override)


def shovel_get(vhost, name, **config_override):
    """
    Get a shovel parameter.

    :param str vhost: The name of the virtual host.
    :param str name: The name of the shovel.
    :param config_override: Optional configuration overrides.
    :return: Shovel definition or None if not found.
    :rtype: dict or None

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.shovel_get / my-shovel
        salt '*' rabbitmq_management.shovel_get production data-mover
    """
    return _parameter_get("shovel", vhost, name, **config_override)


def shovel_list(vhost=None, **config_override):
    """
    List all shovel parameters, optionally filtered by vhost.

    :param str vhost: Optional vhost filter.
    :param config_override: Optional configuration overrides.
    :return: List of shovels.
    :rtype: list

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.shovel_list
        salt '*' rabbitmq_management.shovel_list vhost=/
        salt '*' rabbitmq_management.shovel_list vhost=production
    """
    return _parameter_list(component="shovel", vhost=vhost, **config_override)


def shovel_delete(vhost, name, **config_override):
    """
    Delete a shovel parameter.

    :param str vhost: The name of the virtual host.
    :param str name: The name of the shovel.
    :param config_override: Optional configuration overrides.
    :return: True if successful.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.shovel_delete / my-shovel
        salt '*' rabbitmq_management.shovel_delete production data-mover
    """
    return _parameter_delete("shovel", vhost, name, **config_override)


def shovel_exist(vhost, name, **config_override):
    """
    Check if a shovel parameter exists.

    :param str vhost: The name of the virtual host.
    :param str name: The name of the shovel.
    :param config_override: Optional configuration overrides.
    :return: True if exists, False otherwise.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.shovel_exist / my-shovel
        salt '*' rabbitmq_management.shovel_exist production data-mover
    """
    return _parameter_exist("shovel", vhost, name, **config_override)


# ------------------------------------------------------------------------------
# Vhost Limits Management
# ------------------------------------------------------------------------------
