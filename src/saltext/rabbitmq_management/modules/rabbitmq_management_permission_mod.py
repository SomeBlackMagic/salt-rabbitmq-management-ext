"""RabbitMQ permission management via the Management API."""

from urllib.parse import quote

from salt.exceptions import CommandExecutionError

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _http_request

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


# =============================================================================
# Permissions Management (HTTP API)
# =============================================================================


def permission_list(vhost, **config_override):
    """
    List all permissions for a specific vhost.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.permission_list /
        salt '*' rabbitmq_management.permission_list /myvhost

    Args:
        vhost: Virtual host name

    Returns:
        list: List of dicts with permission information (user, configure, write, read)
    """
    path = f"/api/vhosts/{quote(vhost, safe='')}/permissions"
    return _http_request("GET", path, **config_override)


def permission_get(vhost, user, **config_override):
    """
    Get permissions for a specific user on a specific vhost.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.permission_get / myuser

    Args:
        vhost: Virtual host name
        user: Username

    Returns:
        dict: Permission details (user, vhost, configure, write, read) or None if not found
    """
    try:
        path = f"/api/permissions/{quote(vhost, safe='')}/{quote(user, safe='')}"
        return _http_request("GET", path, **config_override)
    except CommandExecutionError as exc:
        if "404" in str(exc):
            return None
        raise


def permission_set(vhost, user, configure=".*", write=".*", read=".*", **config_override):
    """
    Set permissions for a user on a vhost.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.permission_set / myuser
        salt '*' rabbitmq_management.permission_set / myuser configure='.*' write='.*' read='.*'
        salt '*' rabbitmq_management.permission_set /myvhost myuser configure='^myapp-.*' write='.*' read='.*'

    Args:
        vhost: Virtual host name
        user: Username
        configure: Regex for resources the user can configure (default: '.*')
        write: Regex for resources the user can write to (default: '.*')
        read: Regex for resources the user can read from (default: '.*')

    Returns:
        dict: Operation result

    Note:
        Permission regexes control access to queues and exchanges:
        - configure: create/delete/modify resources
        - write: publish messages
        - read: consume messages, get queue/exchange info
    """
    data = {
        "configure": configure,
        "write": write,
        "read": read,
    }

    path = f"/api/permissions/{quote(vhost, safe='')}/{quote(user, safe='')}"
    _http_request("PUT", path, data=data, **config_override)

    return {
        "status": "set",
        "vhost": vhost,
        "user": user,
        "configure": configure,
        "write": write,
        "read": read,
    }


def permission_delete(vhost, user, **config_override):
    """
    Delete permissions for a user on a vhost.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.permission_delete / myuser

    Args:
        vhost: Virtual host name
        user: Username

    Returns:
        dict: Operation result
    """
    path = f"/api/permissions/{quote(vhost, safe='')}/{quote(user, safe='')}"
    _http_request("DELETE", path, **config_override)

    return {"status": "deleted", "vhost": vhost, "user": user}


def permission_exist(vhost, user, **config_override):
    """
    Check if permissions exist for a user on a vhost.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.permission_exist / myuser

    Args:
        vhost: Virtual host name
        user: Username

    Returns:
        bool: True if permissions exist, False otherwise
    """
    result = permission_get(vhost, user, **config_override)
    return result is not None


def permission_list_all(**config_override):
    """
    List all permissions across all vhosts.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.permission_list_all

    Returns:
        list: List of all permissions (user, vhost, configure, write, read)
    """
    return _http_request("GET", "/api/permissions", **config_override)


def topic_permission_list(vhost, **config_override):
    """
    List all topic permissions for a specific vhost.

    Topic permissions control access to specific topics in topic exchanges.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.topic_permission_list /

    Args:
        vhost: Virtual host name

    Returns:
        list: List of topic permissions
    """
    path = f"/api/vhosts/{quote(vhost, safe='')}/topic-permissions"
    return _http_request("GET", path, **config_override)


def topic_permission_get(vhost, user, **config_override):
    """
    Get topic permissions for a specific user on a vhost.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.topic_permission_get / myuser

    Args:
        vhost: Virtual host name
        user: Username

    Returns:
        list: List of topic permissions for the user or None if not found
    """
    try:
        path = f"/api/topic-permissions/{quote(vhost, safe='')}/{quote(user, safe='')}"
        return _http_request("GET", path, **config_override)
    except CommandExecutionError as exc:
        if "404" in str(exc):
            return None
        raise


def topic_permission_set(vhost, user, exchange, write, read, **config_override):
    """
    Set topic permissions for a user on a vhost.

    Topic permissions provide fine-grained access control for topic exchanges.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.topic_permission_set / myuser amq.topic '^orders\\..*' '^orders\\..*'

    Args:
        vhost: Virtual host name
        user: Username
        exchange: Exchange name (usually a topic exchange)
        write: Regex for routing keys the user can publish to
        read: Regex for routing keys the user can consume from

    Returns:
        dict: Operation result
    """
    data = {
        "exchange": exchange,
        "write": write,
        "read": read,
    }

    path = f"/api/topic-permissions/{quote(vhost, safe='')}/{quote(user, safe='')}"
    _http_request("PUT", path, data=data, **config_override)

    return {
        "status": "set",
        "vhost": vhost,
        "user": user,
        "exchange": exchange,
        "write": write,
        "read": read,
    }


def topic_permission_delete(vhost, user, **config_override):
    """
    Delete all topic permissions for a user on a vhost.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.topic_permission_delete / myuser

    Args:
        vhost: Virtual host name
        user: Username

    Returns:
        dict: Operation result
    """
    path = f"/api/topic-permissions/{quote(vhost, safe='')}/{quote(user, safe='')}"
    _http_request("DELETE", path, **config_override)

    return {"status": "deleted", "vhost": vhost, "user": user}


def topic_permission_delete_specific(vhost, user, exchange, **config_override):
    """
    Delete topic permission for a user on a specific exchange.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.topic_permission_delete_specific / myuser amq.topic

    Args:
        vhost: Virtual host name
        user: Username
        exchange: Exchange name

    Returns:
        dict: Operation result
    """
    path = f"/api/topic-permissions/{quote(vhost, safe='')}/{quote(user, safe='')}/{quote(exchange, safe='')}"
    _http_request("DELETE", path, **config_override)

    return {"status": "deleted", "vhost": vhost, "user": user, "exchange": exchange}
