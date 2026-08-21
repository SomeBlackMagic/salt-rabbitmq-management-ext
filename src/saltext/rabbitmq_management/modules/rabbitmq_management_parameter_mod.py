"""RabbitMQ runtime parameter management via the Management API."""

from urllib.parse import quote

import salt.utils.json
from salt.exceptions import CommandExecutionError

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _http_request

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


# =============================================================================
# Parameters Management (HTTP API)
# =============================================================================


def parameter_list(component=None, vhost=None, **config_override):
    """
    List all parameters, optionally filtered by component and/or vhost.

    CLI Examples:

    .. code-block:: bash

        # List all parameters
        salt '*' rabbitmq_management.parameter_list

        # List federation parameters
        salt '*' rabbitmq_management.parameter_list component=federation

        # List parameters in specific vhost
        salt '*' rabbitmq_management.parameter_list vhost=/production

        # List federation parameters in specific vhost
        salt '*' rabbitmq_management.parameter_list component=federation vhost=/

    Args:
        component: Parameter component (federation, shovel, etc.) (optional)
        vhost: Virtual host name (optional)

    Returns:
        list: List of parameters
    """
    if component and vhost:
        path = f"/api/parameters/{quote(component, safe='')}/{quote(vhost, safe='')}"
    elif component:
        path = f"/api/parameters/{quote(component, safe='')}"
    else:
        path = "/api/parameters"

    return _http_request("GET", path, **config_override)


def parameter_get(component, vhost, name, **config_override):
    """
    Get a specific parameter.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.parameter_get federation / my-upstream
        salt '*' rabbitmq_management.parameter_get shovel / my-shovel

    Args:
        component: Parameter component (federation, shovel, etc.)
        vhost: Virtual host name
        name: Parameter name

    Returns:
        dict: Parameter details or None if not found
    """
    try:
        path = f"/api/parameters/{quote(component, safe='')}/{quote(vhost, safe='')}/{quote(name, safe='')}"
        return _http_request("GET", path, **config_override)
    except CommandExecutionError as exc:
        if "404" in str(exc):
            return None
        raise


def parameter_create(component, vhost, name, value, **config_override):
    """
    Create or update a parameter.

    CLI Examples:

    .. code-block:: bash

        # Federation upstream
        salt '*' rabbitmq_management.parameter_create federation / my-upstream \\
            '{"uri":"amqp://server","expires":3600000}'

        # Shovel
        salt '*' rabbitmq_management.parameter_create shovel / my-shovel \\
            '{"src-uri":"amqp://","src-queue":"source","dest-uri":"amqp://dest","dest-queue":"destination"}'

        # Federation upstream set
        salt '*' rabbitmq_management.parameter_create federation-upstream-set / my-set \\
            '[{"upstream":"upstream1"},{"upstream":"upstream2"}]'

    Args:
        component: Parameter component (federation, shovel, federation-upstream-set, etc.)
        vhost: Virtual host name
        name: Parameter name
        value: Parameter value as dict or JSON string

    Returns:
        dict: Operation result
    """
    if isinstance(value, str):
        value = salt.utils.json.loads(value)

    data = {"value": value}

    path = f"/api/parameters/{quote(component, safe='')}/{quote(vhost, safe='')}/{quote(name, safe='')}"
    _http_request("PUT", path, data=data, **config_override)

    return {"status": "created", "component": component, "vhost": vhost, "name": name}


def parameter_delete(component, vhost, name, **config_override):
    """
    Delete a parameter.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.parameter_delete federation / my-upstream
        salt '*' rabbitmq_management.parameter_delete shovel / my-shovel

    Args:
        component: Parameter component
        vhost: Virtual host name
        name: Parameter name

    Returns:
        dict: Operation result
    """
    path = f"/api/parameters/{quote(component, safe='')}/{quote(vhost, safe='')}/{quote(name, safe='')}"
    _http_request("DELETE", path, **config_override)

    return {"status": "deleted", "component": component, "vhost": vhost, "name": name}


def parameter_exist(component, vhost, name, **config_override):
    """
    Check if a parameter exists.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.parameter_exist federation / my-upstream

    Args:
        component: Parameter component
        vhost: Virtual host name
        name: Parameter name

    Returns:
        bool: True if parameter exists, False otherwise
    """
    result = parameter_get(component, vhost, name, **config_override)
    return result is not None


# Convenience functions for common parameter types
