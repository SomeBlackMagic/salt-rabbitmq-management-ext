"""RabbitMQ virtual host management via the Management API."""

from urllib.parse import quote

from salt.exceptions import CommandExecutionError

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _http_request

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


# =============================================================================
# Virtual Hosts Management (HTTP API)
# =============================================================================


def vhost_list(**config_override):
    """
    List all virtual hosts.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.vhost_list

    Returns:
        list: List of dicts with vhost information
    """
    return _http_request("GET", "/api/vhosts", **config_override)


def vhost_get(name, **config_override):
    """
    Get information about a specific virtual host.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.vhost_get /

    Args:
        name: Virtual host name

    Returns:
        dict: Virtual host details or None if not found
    """
    try:
        path = f"/api/vhosts/{quote(name, safe='')}"
        return _http_request("GET", path, **config_override)
    except CommandExecutionError as exc:
        if "404" in str(exc):
            return None
        raise


def vhost_create(
    name, description=None, tags=None, default_queue_type=None, tracing=False, **config_override
):
    """
    Create a new virtual host.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.vhost_create /myvhost
        salt '*' rabbitmq_management.vhost_create /myvhost description="Production VHost" tags="production"

    Args:
        name: Virtual host name
        description: Optional description
        tags: Optional comma-separated tags or list
        default_queue_type: Default queue type (classic, quorum, stream)
        tracing: Enable tracing (default: False)

    Returns:
        dict: Operation result
    """
    data = {"tracing": tracing}

    if description is not None:
        data["description"] = description

    if tags is not None:
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        data["tags"] = tags

    if default_queue_type:
        data["default_queue_type"] = default_queue_type

    path = f"/api/vhosts/{quote(name, safe='')}"
    _http_request("PUT", path, data=data, **config_override)

    return {"status": "created", "name": name}


def vhost_delete(name, **config_override):
    """
    Delete a virtual host.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.vhost_delete /myvhost

    Args:
        name: Virtual host name

    Returns:
        dict: Operation result
    """
    path = f"/api/vhosts/{quote(name, safe='')}"
    _http_request("DELETE", path, **config_override)

    return {"status": "deleted", "name": name}


def vhost_exist(name, **config_override):
    """
    Check if a virtual host exists.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.vhost_exist /myvhost

    Args:
        name: Virtual host name

    Returns:
        bool: True if vhost exists, False otherwise
    """
    try:
        result = vhost_get(name, **config_override)
        return result is not None
    except CommandExecutionError:
        return False
