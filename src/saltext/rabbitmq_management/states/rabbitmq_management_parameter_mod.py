"""Salt states for managing RabbitMQ runtime parameters."""

import logging

import salt.utils.json

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"

_REQUIRED_FUNCTIONS = (
    "rabbitmq_management.parameter_create",
    "rabbitmq_management.parameter_delete",
    "rabbitmq_management.parameter_exist",
    "rabbitmq_management.parameter_get",
)


def __virtual__():
    """Load only when all required RabbitMQ execution functions are available."""
    missing = [f for f in _REQUIRED_FUNCTIONS if f not in __salt__]
    if missing:
        return False, "Required execution functions are not available: {}".format(
            ", ".join(missing)
        )
    return __virtualname__


def _state_return(name):
    return {"name": name, "result": True, "changes": {}, "comment": ""}


def parameter_present(name, component, vhost, value, **connection_args):
    """
    Ensure a RabbitMQ runtime parameter exists with the desired value.

    When the parameter exists but its ``value`` differs from the desired configuration,
    the parameter is updated via a PUT call to the Management API.

    Args:
        name: Parameter name
        component: Parameter component (federation-upstream, shovel, etc.)
        vhost: Virtual host name
        value: Desired parameter value as a dict or JSON string
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        federation_upstream:
          rabbitmq_management.parameter_present:
            - name: remote-dc
            - component: federation-upstream
            - vhost: /
            - value:
                uri: amqp://remote-server
                expires: 3600000
                prefetch-count: 1000

        shovel_config:
          rabbitmq_management.parameter_present:
            - name: data-mover
            - component: shovel
            - vhost: /
            - value:
                src-uri: amqp://source
                src-queue: source-queue
                dest-uri: amqp://destination
                dest-queue: dest-queue
    """
    ret = _state_return(name)

    if isinstance(value, str):
        value = salt.utils.json.loads(value)

    try:
        current = __salt__["rabbitmq_management.parameter_get"](
            component, vhost, name, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to get parameter %s (component: %s)", name, component)
        ret["result"] = False
        ret["comment"] = f"Failed to get parameter '{name}' (component: {component}): {err}"
        return ret

    if current is None:
        ret["changes"] = {
            "old": None,
            "new": {"component": component, "vhost": vhost, "name": name, "value": value},
        }
        if __opts__.get("test", False):
            ret["result"] = None
            ret["comment"] = f"Parameter '{name}' (component: {component}) would be created"
            return ret
        try:
            __salt__["rabbitmq_management.parameter_create"](
                component, vhost, name, value, **connection_args
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            log.exception("Failed to create parameter %s (component: %s)", name, component)
            ret["result"] = False
            ret["changes"] = {}
            ret["comment"] = f"Failed to create parameter '{name}' (component: {component}): {err}"
            return ret
        ret["comment"] = f"Parameter '{name}' (component: {component}) created"
        return ret

    current_value = current.get("value", {})
    if current_value == value:
        ret["comment"] = (
            f"Parameter '{name}' (component: {component}) is already in the desired state"
        )
        return ret

    ret["changes"] = {
        "old": {"value": current_value},
        "new": {"value": value},
    }
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Parameter '{name}' (component: {component}) would be updated"
        return ret

    try:
        __salt__["rabbitmq_management.parameter_create"](
            component, vhost, name, value, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to update parameter %s (component: %s)", name, component)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to update parameter '{name}' (component: {component}): {err}"
        return ret

    ret["comment"] = f"Parameter '{name}' (component: {component}) updated"
    return ret


def parameter_absent(name, component, vhost, **connection_args):
    """
    Ensure a RabbitMQ runtime parameter does not exist.

    Args:
        name: Parameter name
        component: Parameter component (federation-upstream, shovel, etc.)
        vhost: Virtual host name
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        remove_old_upstream:
          rabbitmq_management.parameter_absent:
            - name: old-upstream
            - component: federation-upstream
            - vhost: /
    """
    ret = _state_return(name)

    try:
        exists = __salt__["rabbitmq_management.parameter_exist"](
            component, vhost, name, **connection_args
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to check parameter %s (component: %s)", name, component)
        ret["result"] = False
        ret["comment"] = f"Failed to check parameter '{name}' (component: {component}): {err}"
        return ret

    if not exists:
        ret["comment"] = (
            f"Parameter '{name}' (component: {component}) on vhost '{vhost}' is already absent"
        )
        return ret

    ret["changes"] = {"old": name, "new": None}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Parameter '{name}' (component: {component}) would be removed"
        return ret

    try:
        __salt__["rabbitmq_management.parameter_delete"](component, vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove parameter %s (component: %s)", name, component)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to remove parameter '{name}' (component: {component}): {err}"
        return ret

    ret["comment"] = f"Parameter '{name}' (component: {component}) removed"
    return ret
