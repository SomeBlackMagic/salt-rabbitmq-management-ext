"""RabbitMQ user management via the Management API."""

from urllib.parse import quote

import salt.utils.json
from salt.exceptions import CommandExecutionError

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _http_request

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


# =============================================================================
# Users Management (HTTP API)
# =============================================================================


def user_list(**config_override):
    """
    List all users.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_list

    Returns:
        list: List of dicts with user information (name, password_hash, hashing_algorithm, tags)
    """
    return _http_request("GET", "/api/users", **config_override)


def user_get(name, **config_override):
    """
    Get information about a specific user.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_get guest

    Args:
        name: Username

    Returns:
        dict: User details or None if not found
    """
    try:
        path = f"/api/users/{quote(name, safe='')}"
        return _http_request("GET", path, **config_override)
    except CommandExecutionError as exc:
        if "404" in str(exc):
            return None
        raise


def user_create(name, password=None, tags=None, hashing_algorithm=None, **config_override):
    """
    Create a new user.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_create myuser password=secret tags=administrator
        salt '*' rabbitmq_management.user_create myuser tags="monitoring,management"
        salt '*' rabbitmq_management.user_create myuser password=secret tags='["administrator"]'

    Args:
        name: Username
        password: Password (if None, user will be created without password - auth via certificates/external)
        tags: User tags (administrator, monitoring, management, policymaker, impersonator) as:
              - string: comma-separated "administrator,monitoring"
              - list: ["administrator", "monitoring"]
        hashing_algorithm: Password hashing algorithm (rabbit_password_hashing_sha256, rabbit_password_hashing_sha512, rabbit_password_hashing_md5)

    Returns:
        dict: Operation result
    """
    data = {}

    if password is not None:
        data["password"] = password
        if hashing_algorithm:
            data["hashing_algorithm"] = hashing_algorithm

    if tags is not None:
        if isinstance(tags, str):
            # Handle both comma-separated and JSON array strings
            if tags.startswith("["):
                tags = salt.utils.json.loads(tags)
            else:
                tags = [t.strip() for t in tags.split(",")]
        data["tags"] = ",".join(tags) if isinstance(tags, list) else tags

    path = f"/api/users/{quote(name, safe='')}"
    _http_request("PUT", path, data=data, **config_override)

    return {"status": "created", "name": name}


def user_delete(name, **config_override):
    """
    Delete a user.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_delete myuser

    Args:
        name: Username

    Returns:
        dict: Operation result
    """
    path = f"/api/users/{quote(name, safe='')}"
    _http_request("DELETE", path, **config_override)

    return {"status": "deleted", "name": name}


def user_exist(name, **config_override):
    """
    Check if a user exists.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_exist myuser

    Args:
        name: Username

    Returns:
        bool: True if user exists, False otherwise
    """
    try:
        result = user_get(name, **config_override)
        return result is not None
    except CommandExecutionError:
        return False


def user_set_password(name, password, hashing_algorithm=None, **config_override):
    """
    Change user password.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_set_password myuser new_password

    Args:
        name: Username
        password: New password
        hashing_algorithm: Password hashing algorithm (optional)

    Returns:
        dict: Operation result
    """
    data = {"password": password}

    if hashing_algorithm:
        data["hashing_algorithm"] = hashing_algorithm

    path = f"/api/users/{quote(name, safe='')}"
    _http_request("PUT", path, data=data, **config_override)

    return {"status": "password_changed", "name": name}


def user_set_tags(name, tags, **config_override):
    """
    Set user tags (roles).

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_set_tags myuser administrator
        salt '*' rabbitmq_management.user_set_tags myuser "monitoring,management"
        salt '*' rabbitmq_management.user_set_tags myuser '["administrator"]'

    Args:
        name: Username
        tags: User tags as string (comma-separated) or list
              Available tags: administrator, monitoring, management, policymaker, impersonator

    Returns:
        dict: Operation result
    """
    if isinstance(tags, str):
        if tags.startswith("["):
            tags = salt.utils.json.loads(tags)
        else:
            tags = [t.strip() for t in tags.split(",")]

    tags_str = ",".join(tags) if isinstance(tags, list) else tags

    data = {"tags": tags_str}
    path = f"/api/users/{quote(name, safe='')}"
    _http_request("PUT", path, data=data, **config_override)

    return {"status": "tags_set", "name": name, "tags": tags_str}


def user_get_permissions(name, **config_override):
    """
    Get all permissions for a specific user across all vhosts.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_get_permissions myuser

    Args:
        name: Username

    Returns:
        list: List of permissions per vhost
    """
    path = f"/api/users/{quote(name, safe='')}/permissions"
    return _http_request("GET", path, **config_override)


def user_without_permissions(**config_override):
    """
    List all users that don't have permissions to any vhost.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_without_permissions

    Returns:
        list: List of usernames without permissions
    """
    path = "/api/users/without-permissions"
    return _http_request("GET", path, **config_override)


def user_bulk_delete(users, **config_override):
    """
    Delete multiple users.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_bulk_delete '["user1", "user2", "user3"]'

    Args:
        users: List of usernames to delete

    Returns:
        dict: Operation results
    """
    if isinstance(users, str):
        users = salt.utils.json.loads(users)

    data = {"users": users}
    path = "/api/users/bulk-delete"
    _http_request("POST", path, data=data, **config_override)

    return {"status": "deleted", "users": users}


def user_check_password(name, password, **config_override):
    """
    Check if a user's password is valid by attempting authentication.

    This function tests if the given username and password are valid
    by making a test request to the RabbitMQ Management API with these credentials.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.user_check_password myuser mypassword

    Args:
        name: Username
        password: Password to check

    Returns:
        bool: True if authentication succeeds, False otherwise
    """
    # Override management credentials with the ones we want to test
    test_config = config_override.copy()
    test_config["management_user"] = name
    test_config["management_password"] = password

    try:
        # Try to access the whoami endpoint - lightweight check
        result = _http_request("GET", "/api/whoami", **test_config)

        # If we got here, authentication succeeded
        # Verify the username matches
        if result.get("name") == name:
            return True
        return False
    except CommandExecutionError:
        # Authentication failed
        return False
