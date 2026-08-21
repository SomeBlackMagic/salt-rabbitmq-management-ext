"""RabbitMQ virtual host and user limit management via the Management API."""

from urllib.parse import quote

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _http_request

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


def vhost_limit_list(vhost, **config_override):
    """
    List all limits for a specific virtual host.

    :param str vhost: The name of the virtual host.
    :param config_override: Optional configuration overrides.
    :return: List of limit definitions for the vhost.
    :rtype: list

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.vhost_limit_list /
        salt '*' rabbitmq_management.vhost_limit_list production
    """
    vhost_encoded = quote(vhost, safe="")
    path = f"/api/vhost-limits/{vhost_encoded}"
    result = _http_request("GET", path, **config_override)
    return result


def vhost_limit_get(vhost, limit_type, **config_override):
    """
    Get a specific limit for a virtual host.

    :param str vhost: The name of the virtual host.
    :param str limit_type: The type of limit (max-connections or max-queues).
    :param config_override: Optional configuration overrides.
    :return: Limit definition or None if not set.
    :rtype: dict or None

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.vhost_limit_get / max-connections
        salt '*' rabbitmq_management.vhost_limit_get production max-queues
    """
    limits = vhost_limit_list(vhost, **config_override)
    for limit in limits:
        if limit.get("name") == limit_type:
            return limit
    return None


def vhost_limit_set(vhost, limit_type, value, **config_override):
    """
    Set a limit for a virtual host.

    :param str vhost: The name of the virtual host.
    :param str limit_type: The type of limit (max-connections or max-queues).
    :param int value: The limit value (-1 for unlimited).
    :param config_override: Optional configuration overrides.
    :return: True if successful.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.vhost_limit_set / max-connections 1000
        salt '*' rabbitmq_management.vhost_limit_set production max-queues 500
        salt '*' rabbitmq_management.vhost_limit_set / max-connections -1  # unlimited
    """
    vhost_encoded = quote(vhost, safe="")
    limit_encoded = quote(limit_type, safe="")
    path = f"/api/vhost-limits/{vhost_encoded}/{limit_encoded}"
    data = {"value": value}
    _http_request("PUT", path, data=data, **config_override)
    return True


def vhost_limit_delete(vhost, limit_type, **config_override):
    """
    Delete a limit for a virtual host (removes the limit, making it unlimited).

    :param str vhost: The name of the virtual host.
    :param str limit_type: The type of limit (max-connections or max-queues).
    :param config_override: Optional configuration overrides.
    :return: True if successful.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.vhost_limit_delete / max-connections
        salt '*' rabbitmq_management.vhost_limit_delete production max-queues
    """
    vhost_encoded = quote(vhost, safe="")
    limit_encoded = quote(limit_type, safe="")
    path = f"/api/vhost-limits/{vhost_encoded}/{limit_encoded}"
    _http_request("DELETE", path, **config_override)
    return True


def vhost_limit_exist(vhost, limit_type, **config_override):
    """
    Check if a specific limit is set for a virtual host.

    :param str vhost: The name of the virtual host.
    :param str limit_type: The type of limit (max-connections or max-queues).
    :param config_override: Optional configuration overrides.
    :return: True if the limit exists, False otherwise.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.vhost_limit_exist / max-connections
        salt '*' rabbitmq_management.vhost_limit_exist production max-queues
    """
    limit = vhost_limit_get(vhost, limit_type, **config_override)
    return limit is not None


# ------------------------------------------------------------------------------
# User Limits Management
# ------------------------------------------------------------------------------


def user_limit_list(user, **config_override):
    """
    List all limits for a specific user.

    :param str user: The name of the user.
    :param config_override: Optional configuration overrides.
    :return: List of limit definitions for the user.
    :rtype: list

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_limit_list guest
        salt '*' rabbitmq_management.user_limit_list app_user
    """
    user_encoded = quote(user, safe="")
    path = f"/api/user-limits/{user_encoded}"
    result = _http_request("GET", path, **config_override)
    return result


def user_limit_get(user, limit_type, **config_override):
    """
    Get a specific limit for a user.

    :param str user: The name of the user.
    :param str limit_type: The type of limit (max-connections or max-channels).
    :param config_override: Optional configuration overrides.
    :return: Limit definition or None if not set.
    :rtype: dict or None

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_limit_get guest max-connections
        salt '*' rabbitmq_management.user_limit_get app_user max-channels
    """
    limits = user_limit_list(user, **config_override)
    for limit in limits:
        if limit.get("name") == limit_type:
            return limit
    return None


def user_limit_set(user, limit_type, value, **config_override):
    """
    Set a limit for a user.

    :param str user: The name of the user.
    :param str limit_type: The type of limit (max-connections or max-channels).
    :param int value: The limit value (-1 for unlimited).
    :param config_override: Optional configuration overrides.
    :return: True if successful.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_limit_set guest max-connections 100
        salt '*' rabbitmq_management.user_limit_set app_user max-channels 500
        salt '*' rabbitmq_management.user_limit_set guest max-connections -1  # unlimited
    """
    user_encoded = quote(user, safe="")
    limit_encoded = quote(limit_type, safe="")
    path = f"/api/user-limits/{user_encoded}/{limit_encoded}"
    data = {"value": value}
    _http_request("PUT", path, data=data, **config_override)
    return True


def user_limit_delete(user, limit_type, **config_override):
    """
    Delete a limit for a user (removes the limit, making it unlimited).

    :param str user: The name of the user.
    :param str limit_type: The type of limit (max-connections or max-channels).
    :param config_override: Optional configuration overrides.
    :return: True if successful.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_limit_delete guest max-connections
        salt '*' rabbitmq_management.user_limit_delete app_user max-channels
    """
    user_encoded = quote(user, safe="")
    limit_encoded = quote(limit_type, safe="")
    path = f"/api/user-limits/{user_encoded}/{limit_encoded}"
    _http_request("DELETE", path, **config_override)
    return True


def user_limit_exist(user, limit_type, **config_override):
    """
    Check if a specific limit is set for a user.

    :param str user: The name of the user.
    :param str limit_type: The type of limit (max-connections or max-channels).
    :param config_override: Optional configuration overrides.
    :return: True if the limit exists, False otherwise.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_limit_exist guest max-connections
        salt '*' rabbitmq_management.user_limit_exist app_user max-channels
    """
    limit = user_limit_get(user, limit_type, **config_override)
    return limit is not None
