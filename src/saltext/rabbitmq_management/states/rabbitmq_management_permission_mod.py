"""
Salt states for managing RabbitMQ permissions.

Permissions in RabbitMQ control what resources a user can access on a virtual
host. Each permission set consists of three regular expressions:

- **configure**: resources the user may declare, delete, or modify
- **write**: resources the user may publish messages to
- **read**: resources the user may consume from or inspect

All three regexes are matched against resource names (queues and exchanges).
An empty string ``""`` denies all access; ``".*"`` grants full access.

States provided by this module:

- :py:func:`permission_present` — ensure permissions are set to the desired values
- :py:func:`permission_absent` — ensure permissions do not exist
"""

import logging

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"

_REQUIRED_FUNCTIONS = (
    "rabbitmq_management.permission_set",
    "rabbitmq_management.permission_delete",
    "rabbitmq_management.permission_exist",
    "rabbitmq_management.permission_get",
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


def permission_present(name, user, configure=".*", write=".*", read=".*", **connection_args):
    """
    Ensure a RabbitMQ user has the specified permissions on a virtual host.

    The ``name`` parameter is used as the virtual host identifier. Each of the
    three permission fields (``configure``, ``write``, ``read``) is a regular
    expression matched against resource names. The defaults grant full access
    to all resources.

    When the permission already exists with identical values the state returns
    without making any API calls. When the values differ only the changed
    fields are reported in ``changes``.

    Args:
        name: Virtual host name (used as the resource identifier)
        user: RabbitMQ user name
        configure: Regex for resources the user may declare, delete, or modify
            (default: ``.*``)
        write: Regex for resources the user may publish messages to
            (default: ``.*``)
        read: Regex for resources the user may consume from or inspect
            (default: ``.*``)
        **connection_args: Optional connection parameter overrides passed to
            every underlying execution-module call

    Example — grant full access:

    .. code-block:: yaml

        myapp_permissions:
          rabbitmq_management.permission_present:
            - name: /production
            - user: myapp

    Example — restrict configure access:

    .. code-block:: yaml

        myapp_restricted:
          rabbitmq_management.permission_present:
            - name: /production
            - user: myapp
            - configure: ^myapp-.*
            - write: .*
            - read: .*

    Example — read-only user:

    .. code-block:: yaml

        readonly_user:
          rabbitmq_management.permission_present:
            - name: /
            - user: reporting
            - configure: ''
            - write: ''
            - read: .*
    """
    ret = _state_return(name)

    try:
        current = __salt__["rabbitmq_management.permission_get"](
            vhost=name, user=user, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to get RabbitMQ permission for user %s on vhost %s", user, name)
        ret["result"] = False
        ret["comment"] = f"Failed to get permission for user '{user}' on vhost '{name}': {err}"
        return ret

    desired = {"configure": configure, "write": write, "read": read}

    if current is None:
        changes = {
            "old": None,
            "new": {"vhost": name, "user": user, **desired},
        }
        if __opts__.get("test", False):
            ret["result"] = None
            ret["changes"] = changes
            ret["comment"] = f"Permission for user '{user}' on vhost '{name}' would be set"
            return ret

        try:
            __salt__["rabbitmq_management.permission_set"](
                vhost=name,
                user=user,
                configure=configure,
                write=write,
                read=read,
                **connection_args,
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            log.exception("Failed to set RabbitMQ permission for user %s on vhost %s", user, name)
            ret["result"] = False
            ret["comment"] = f"Failed to set permission for user '{user}' on vhost '{name}': {err}"
            return ret

        ret["changes"] = changes
        ret["comment"] = f"Permission for user '{user}' on vhost '{name}' set"
        return ret

    fields = ("configure", "write", "read")
    old = {}
    new = {}
    for field in fields:
        if current.get(field) != desired[field]:
            old[field] = current.get(field)
            new[field] = desired[field]

    if not new:
        ret["comment"] = (
            f"Permission for user '{user}' on vhost '{name}' is already in the desired state"
        )
        return ret

    changes = {"old": old, "new": new}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["changes"] = changes
        ret["comment"] = f"Permission for user '{user}' on vhost '{name}' would be updated"
        return ret

    try:
        __salt__["rabbitmq_management.permission_set"](
            vhost=name, user=user, configure=configure, write=write, read=read, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to update RabbitMQ permission for user %s on vhost %s", user, name)
        ret["result"] = False
        ret["comment"] = f"Failed to update permission for user '{user}' on vhost '{name}': {err}"
        return ret

    ret["changes"] = changes
    ret["comment"] = f"Permission for user '{user}' on vhost '{name}' updated"
    return ret


def permission_absent(name, user, **connection_args):
    """
    Ensure a RabbitMQ user has no permissions on a virtual host.

    The ``name`` parameter is used as the virtual host identifier. When no
    permission record exists for the user on the virtual host, the state
    returns without making any API calls.

    Args:
        name: Virtual host name (used as the resource identifier)
        user: RabbitMQ user name
        **connection_args: Optional connection parameter overrides passed to
            every underlying execution-module call

    Example:

    .. code-block:: yaml

        remove_old_permissions:
          rabbitmq_management.permission_absent:
            - name: /old-vhost
            - user: olduser
    """
    ret = _state_return(name)

    try:
        exists = __salt__["rabbitmq_management.permission_exist"](
            vhost=name, user=user, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to check RabbitMQ permission for user %s on vhost %s", user, name)
        ret["result"] = False
        ret["comment"] = f"Failed to check permission for user '{user}' on vhost '{name}': {err}"
        return ret

    if not exists:
        ret["comment"] = f"Permission for user '{user}' on vhost '{name}' is already absent"
        return ret

    changes = {"old": {"vhost": name, "user": user}, "new": None}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["changes"] = changes
        ret["comment"] = f"Permission for user '{user}' on vhost '{name}' would be removed"
        return ret

    try:
        __salt__["rabbitmq_management.permission_delete"](vhost=name, user=user, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove RabbitMQ permission for user %s on vhost %s", user, name)
        ret["result"] = False
        ret["comment"] = f"Failed to remove permission for user '{user}' on vhost '{name}': {err}"
        return ret

    ret["changes"] = changes
    ret["comment"] = f"Permission for user '{user}' on vhost '{name}' removed"
    return ret
