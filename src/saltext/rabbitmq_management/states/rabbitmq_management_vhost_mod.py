"""Salt states for managing RabbitMQ virtual hosts."""

import logging

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"

_REQUIRED_FUNCTIONS = (
    "rabbitmq_management.vhost_create",
    "rabbitmq_management.vhost_delete",
    "rabbitmq_management.vhost_exist",
    "rabbitmq_management.vhost_get",
    "rabbitmq_management.vhost_limit_get",
    "rabbitmq_management.vhost_limit_set",
    "rabbitmq_management.vhost_limit_delete",
    "rabbitmq_management.vhost_limit_exist",
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


def _desired_config(description, tags, default_queue_type, tracing):
    """Build the subset of vhost configuration managed by the state."""
    desired = {}
    if description is not None:
        desired["description"] = description
    if tags is not None:
        desired["tags"] = _normalize_tags(tags)
    if default_queue_type is not None:
        desired["default_queue_type"] = default_queue_type
    if tracing is not None:
        desired["tracing"] = tracing
    return desired


def _config_changes(current, desired):
    """Return old and new values for fields that differ."""
    old = {}
    new = {}

    for key, desired_value in desired.items():
        current_value = current.get(key)
        if key == "description":
            current_value = current.get(key, "")
        elif key == "tags":
            current_value = _normalize_tags(current.get(key) or [])
            if set(current_value) == set(desired_value):
                continue

        if current_value != desired_value:
            old[key] = current_value
            new[key] = desired_value

    return old, new


def vhost_present(
    name,
    description=None,
    tags=None,
    default_queue_type=None,
    tracing=None,
    **connection_args,
):
    """
    Ensure a RabbitMQ virtual host exists with the requested configuration.

    ``None`` means that an optional field is not managed. Empty descriptions and
    tag lists are explicit values and can therefore be used to clear a field.

    Args:
        name: Virtual host name
        description: Optional description for the vhost
        tags: Optional tags (comma-separated string or list)
        default_queue_type: Default queue type (classic, quorum, stream)
        tracing: Enable or disable tracing; leave as ``None`` to preserve it
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        production_vhost:
          rabbitmq_management.vhost_present:
            - name: /production
            - description: Production environment vhost
            - tags:
              - production
              - critical
            - default_queue_type: quorum
            - tracing: false
    """
    ret = _state_return(name)

    try:
        desired = _desired_config(description, tags, default_queue_type, tracing)
    except (TypeError, ValueError) as err:
        ret["result"] = False
        ret["comment"] = f"Invalid vhost configuration: {err}"
        return ret

    try:
        vhost_exists = __salt__["rabbitmq_management.vhost_exist"](name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to check whether vhost %s exists", name)
        ret["result"] = False
        ret["comment"] = f"Failed to check vhost existence: {err}"
        return ret

    current_config = None
    old = {}
    new = desired.copy()
    if vhost_exists:
        try:
            current_config = __salt__["rabbitmq_management.vhost_get"](name, **connection_args)
        except Exception as err:  # pylint: disable=broad-exception-caught
            log.exception("Failed to get configuration for vhost %s", name)
            ret["result"] = False
            ret["comment"] = f"Failed to get vhost configuration: {err}"
            return ret

        if not isinstance(current_config, dict):
            ret["result"] = False
            ret["comment"] = f"Vhost '{name}' exists, but its configuration could not be retrieved"
            return ret

        try:
            old, new = _config_changes(current_config, desired)
        except (TypeError, ValueError) as err:
            ret["result"] = False
            ret["comment"] = f"Invalid vhost configuration returned by RabbitMQ: {err}"
            return ret

    changes_needed = not vhost_exists or bool(new)

    if __opts__.get("test", False):
        if not changes_needed:
            ret["comment"] = f"Vhost '{name}' is already in the desired state"
            return ret

        ret["result"] = None
        if vhost_exists:
            ret["comment"] = f"Vhost '{name}' would be updated"
            ret["changes"] = {"old": old, "new": new}
        else:
            ret["comment"] = f"Vhost '{name}' would be created"
            ret["changes"] = {"old": None, "new": {"name": name, **desired}}
        return ret

    if not changes_needed:
        ret["comment"] = f"Vhost '{name}' already exists with the correct configuration"
        return ret

    try:
        __salt__["rabbitmq_management.vhost_create"](name, **desired, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to create or update vhost %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to create/update vhost '{name}': {err}"
        return ret

    if vhost_exists:
        ret["comment"] = f"Vhost '{name}' updated"
        ret["changes"] = {"old": old, "new": new}
    else:
        ret["comment"] = f"Vhost '{name}' created"
        ret["changes"] = {"old": None, "new": {"name": name, **desired}}

    return ret


def vhost_limit_present(name, limit_type, value, **connection_args):
    """
    Ensure a RabbitMQ virtual host limit is set to the desired value.

    Args:
        name: Virtual host name
        limit_type: Limit type (max-connections or max-queues)
        value: Limit value (-1 for unlimited)
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        production_vhost_connections:
          rabbitmq_management.vhost_limit_present:
            - name: /production
            - limit_type: max-connections
            - value: 1000

        production_vhost_queues:
          rabbitmq_management.vhost_limit_present:
            - name: /production
            - limit_type: max-queues
            - value: 500
    """
    ret = _state_return(name)

    try:
        current = __salt__["rabbitmq_management.vhost_limit_get"](
            name, limit_type, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to get limit '%s' for vhost %s", limit_type, name)
        ret["result"] = False
        ret["comment"] = f"Failed to get limit '{limit_type}' for vhost '{name}': {err}"
        return ret

    if current is None:
        ret["changes"] = {"old": None, "new": {"limit_type": limit_type, "value": value}}
        if __opts__.get("test", False):
            ret["result"] = None
            ret["comment"] = f"Limit '{limit_type}' for vhost '{name}' would be set"
            return ret
        try:
            __salt__["rabbitmq_management.vhost_limit_set"](
                name, limit_type, value, **connection_args
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            log.exception("Failed to set limit '%s' for vhost %s", limit_type, name)
            ret["result"] = False
            ret["changes"] = {}
            ret["comment"] = f"Failed to set limit '{limit_type}' for vhost '{name}': {err}"
            return ret
        ret["comment"] = f"Limit '{limit_type}' for vhost '{name}' set"
        return ret

    if current["value"] == value:
        ret["comment"] = f"Limit '{limit_type}' for vhost '{name}' is already in the desired state"
        return ret

    ret["changes"] = {"old": {"value": current["value"]}, "new": {"value": value}}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Limit '{limit_type}' for vhost '{name}' would be updated"
        return ret

    try:
        __salt__["rabbitmq_management.vhost_limit_set"](name, limit_type, value, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to update limit '%s' for vhost %s", limit_type, name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to update limit '{limit_type}' for vhost '{name}': {err}"
        return ret

    ret["comment"] = f"Limit '{limit_type}' for vhost '{name}' updated"
    return ret


def vhost_limit_absent(name, limit_type, **connection_args):
    """
    Ensure a RabbitMQ virtual host limit is not set.

    Args:
        name: Virtual host name
        limit_type: Limit type (max-connections or max-queues)
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        remove_connection_limit:
          rabbitmq_management.vhost_limit_absent:
            - name: /staging
            - limit_type: max-connections
    """
    ret = _state_return(name)

    try:
        current = __salt__["rabbitmq_management.vhost_limit_get"](
            name, limit_type, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to get limit '%s' for vhost %s", limit_type, name)
        ret["result"] = False
        ret["comment"] = f"Failed to get limit '{limit_type}' for vhost '{name}': {err}"
        return ret

    if current is None:
        ret["comment"] = f"Limit '{limit_type}' for vhost '{name}' is already absent"
        return ret

    ret["changes"] = {"old": {"limit_type": limit_type, "value": current["value"]}, "new": None}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Limit '{limit_type}' for vhost '{name}' would be removed"
        return ret

    try:
        __salt__["rabbitmq_management.vhost_limit_delete"](name, limit_type, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove limit '%s' for vhost %s", limit_type, name)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to remove limit '{limit_type}' for vhost '{name}': {err}"
        return ret

    ret["comment"] = f"Limit '{limit_type}' for vhost '{name}' removed"
    return ret


def vhost_absent(name, **connection_args):
    """
    Ensure a RabbitMQ virtual host does not exist.

    Args:
        name: Virtual host name to remove
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        old_vhost:
          rabbitmq_management.vhost_absent:
            - name: /old-environment
    """
    ret = _state_return(name)

    try:
        vhost_exists = __salt__["rabbitmq_management.vhost_exist"](name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to check whether vhost %s exists", name)
        ret["result"] = False
        ret["comment"] = f"Failed to check vhost existence: {err}"
        return ret

    if not vhost_exists:
        ret["comment"] = f"Vhost '{name}' is already absent"
        return ret

    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Vhost '{name}' would be removed"
        ret["changes"] = {"old": name, "new": None}
        return ret

    try:
        __salt__["rabbitmq_management.vhost_delete"](name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove vhost %s", name)
        ret["result"] = False
        ret["comment"] = f"Failed to remove vhost '{name}': {err}"
        return ret

    ret["comment"] = f"Vhost '{name}' removed"
    ret["changes"] = {"old": name, "new": None}
    return ret
