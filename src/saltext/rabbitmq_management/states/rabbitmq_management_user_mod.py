"""Salt states for managing RabbitMQ users."""

import logging

import salt.utils.sdb

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"

_REQUIRED_FUNCTIONS = (
    "rabbitmq_management.user_create",
    "rabbitmq_management.user_delete",
    "rabbitmq_management.user_exist",
    "rabbitmq_management.user_get",
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


def _normalize_tags(tags):
    """Normalize supported tag representations to a list."""
    if isinstance(tags, str):
        return [tag.strip() for tag in tags.split(",") if tag.strip()]
    if isinstance(tags, list):
        return tags
    raise TypeError("tags must be a comma-separated string or a list")


def _user_changes(current, tags, password):
    """Return changes for the managed fields of an existing user."""
    old = {}
    new = {}

    if tags is not None:
        current_tags = _normalize_tags(current.get("tags") or [])
        if set(current_tags) != set(tags):
            old["tags"] = current_tags
            new["tags"] = tags

    if password is not None:
        old["password_set"] = None
        new["password_set"] = True

    return old, new


def _resolve_password(password):
    """Resolve an SDB password URI, leaving ordinary passwords unchanged."""
    if not isinstance(password, str) or not password.startswith("sdb://"):
        return password

    resolved_password = salt.utils.sdb.sdb_get(password, __opts__, strict=True)
    if not isinstance(resolved_password, str):
        raise TypeError("SDB password must resolve to a string")
    return resolved_password


def user_present(
    name,
    password=None,
    tags=None,
    hashing_algorithm=None,
    **connection_args,
):
    """
    Ensure a RabbitMQ user exists with the requested managed fields.

    A password cannot be compared with the RabbitMQ API response. Whenever
    ``password`` is supplied, it is therefore set again. A value of ``None``
    leaves the password unmanaged. Password values beginning with ``sdb://``
    are resolved through Salt SDB immediately before the user is changed. Tags
    are compared without regard to order.

    Args:
        name: RabbitMQ user name
        password: Optional password to set; ``None`` leaves it unmanaged
        tags: Optional tags as a comma-separated string or list
        hashing_algorithm: Optional RabbitMQ password hashing algorithm
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        myapp_user:
          rabbitmq_management.user_present:
            - name: myapp
            - password: sdb://vault/rabbitmq/myapp/password
            - tags:
              - monitoring
              - management
    """
    ret = _state_return(name)

    try:
        normalized_tags = _normalize_tags(tags) if tags is not None else None
    except (TypeError, ValueError) as err:
        ret["result"] = False
        ret["comment"] = f"Invalid user configuration: {err}"
        return ret

    try:
        current = __salt__["rabbitmq_management.user_get"](name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to get RabbitMQ user %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to get user '{name}': {err}"
        return ret

    user_exists = current is not None
    if user_exists and not isinstance(current, dict):
        ret["result"] = False
        ret["comment"] = f"User '{name}' exists, but its configuration could not be retrieved"
        return ret

    if user_exists:
        try:
            old, new = _user_changes(current, normalized_tags, password)
        except (TypeError, ValueError) as err:
            ret["result"] = False
            ret["comment"] = f"Invalid user configuration returned by RabbitMQ: {err}"
            return ret
        changes = {"old": old, "new": new}
    else:
        changes = {
            "old": None,
            "new": {
                "name": name,
                "tags": normalized_tags or [],
                "password_set": password is not None,
            },
        }

    changes_needed = not user_exists or bool(changes["new"])
    if not changes_needed:
        ret["comment"] = f"User '{name}' already exists with the correct configuration"
        return ret

    if __opts__.get("test", False):
        ret["result"] = None
        ret["changes"] = changes
        if user_exists:
            ret["comment"] = f"User '{name}' would be updated"
        else:
            ret["comment"] = f"User '{name}' would be created"
        return ret

    try:
        resolved_password = _resolve_password(password)
    except Exception:  # pylint: disable=broad-exception-caught
        log.exception("Failed to resolve an SDB password for RabbitMQ user %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to resolve password from SDB for user '{name}'"
        return ret

    try:
        __salt__["rabbitmq_management.user_create"](
            name,
            password=resolved_password,
            tags=normalized_tags,
            hashing_algorithm=hashing_algorithm,
            **connection_args,
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to create or update RabbitMQ user %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to create/update user '{name}': {err}"
        return ret

    ret["changes"] = changes
    if user_exists:
        ret["comment"] = f"User '{name}' updated"
    else:
        ret["comment"] = f"User '{name}' created"
    return ret


def user_absent(name, **connection_args):
    """
    Ensure a RabbitMQ user does not exist.

    Args:
        name: RabbitMQ user name to remove
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        remove_old_user:
          rabbitmq_management.user_absent:
            - name: olduser
    """
    ret = _state_return(name)

    try:
        user_exists = __salt__["rabbitmq_management.user_exist"](name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to check whether RabbitMQ user %s exists", name)
        ret["result"] = False
        ret["comment"] = f"Failed to check user existence: {err}"
        return ret

    if not user_exists:
        ret["comment"] = f"User '{name}' is already absent"
        return ret

    changes = {"old": name, "new": None}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["changes"] = changes
        ret["comment"] = f"User '{name}' would be removed"
        return ret

    try:
        __salt__["rabbitmq_management.user_delete"](name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove RabbitMQ user %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to remove user '{name}': {err}"
        return ret

    ret["changes"] = changes
    ret["comment"] = f"User '{name}' removed"
    return ret
