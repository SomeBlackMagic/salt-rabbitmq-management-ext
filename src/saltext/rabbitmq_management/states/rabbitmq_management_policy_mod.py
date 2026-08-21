"""Salt states for managing RabbitMQ policies."""

import json
import logging

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"

_REQUIRED_FUNCTIONS = (
    "rabbitmq_management.policy_create",
    "rabbitmq_management.policy_delete",
    "rabbitmq_management.policy_exist",
    "rabbitmq_management.policy_get",
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


def policy_present(
    name,
    vhost,
    pattern,
    definition,
    priority=0,
    apply_to="all",
    **connection_args,
):
    """
    Ensure a RabbitMQ policy exists with the desired configuration.

    When the policy exists but its configuration differs from the desired state,
    the policy is updated via the Management API.

    Args:
        name: Policy name
        vhost: Virtual host name
        pattern: Regex pattern to match queue/exchange names
        definition: Policy definition as dict or JSON string
        priority: Policy priority (default: 0, higher number = higher priority)
        apply_to: Apply to: all, queues, exchanges (default: all)
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        ha_policy:
          rabbitmq_management.policy_present:
            - name: ha-all
            - vhost: /
            - pattern: ^.*
            - definition:
                ha-mode: all
                ha-sync-mode: automatic
            - priority: 0
            - apply_to: queues
    """
    ret = _state_return(name)

    if isinstance(definition, str):
        definition = json.loads(definition)

    try:
        current = __salt__["rabbitmq_management.policy_get"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to get policy '%s' on vhost '%s'", name, vhost)
        ret["result"] = False
        ret["comment"] = f"Failed to get policy '{name}' on vhost '{vhost}': {err}"
        return ret

    if current is None:
        ret["changes"] = {
            "old": None,
            "new": {
                "vhost": vhost,
                "name": name,
                "pattern": pattern,
                "definition": definition,
                "priority": priority,
                "apply_to": apply_to,
            },
        }
        if __opts__.get("test", False):
            ret["result"] = None
            ret["comment"] = f"Policy '{name}' would be created"
            return ret
        try:
            __salt__["rabbitmq_management.policy_create"](
                vhost,
                name,
                pattern,
                definition,
                priority=priority,
                apply_to=apply_to,
                **connection_args,
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            log.exception("Failed to create policy '%s' on vhost '%s'", name, vhost)
            ret["result"] = False
            ret["changes"] = {}
            ret["comment"] = f"Failed to create policy '{name}' on vhost '{vhost}': {err}"
            return ret
        ret["comment"] = f"Policy '{name}' created"
        return ret

    # Compare current vs desired
    desired = {
        "pattern": pattern,
        "definition": definition,
        "priority": priority,
        "apply-to": apply_to,
    }
    old_changes = {}
    new_changes = {}
    for api_key, desired_val in desired.items():
        current_val = current.get(api_key)
        if current_val != desired_val:
            display_key = "apply_to" if api_key == "apply-to" else api_key
            old_changes[display_key] = current_val
            new_changes[display_key] = desired_val

    if not old_changes:
        ret["comment"] = f"Policy '{name}' is already in the desired state"
        return ret

    ret["changes"] = {"old": old_changes, "new": new_changes}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Policy '{name}' would be updated"
        return ret

    try:
        __salt__["rabbitmq_management.policy_create"](
            vhost,
            name,
            pattern,
            definition,
            priority=priority,
            apply_to=apply_to,
            **connection_args,
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to update policy '%s' on vhost '%s'", name, vhost)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to update policy '{name}' on vhost '{vhost}': {err}"
        return ret

    ret["comment"] = f"Policy '{name}' updated"
    return ret


def policy_absent(name, vhost, **connection_args):
    """
    Ensure a RabbitMQ policy does not exist.

    Args:
        name: Policy name
        vhost: Virtual host name
        **connection_args: Optional connection parameter overrides

    Example:

    .. code-block:: yaml

        remove_old_policy:
          rabbitmq_management.policy_absent:
            - name: old-ha-policy
            - vhost: /
    """
    ret = _state_return(name)

    try:
        exists = __salt__["rabbitmq_management.policy_exist"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to check policy '%s' on vhost '%s'", name, vhost)
        ret["result"] = False
        ret["comment"] = f"Failed to check policy '{name}' on vhost '{vhost}': {err}"
        return ret

    if not exists:
        ret["comment"] = f"Policy '{name}' on vhost '{vhost}' is already absent"
        return ret

    ret["changes"] = {"old": name, "new": None}
    if __opts__.get("test", False):
        ret["result"] = None
        ret["comment"] = f"Policy '{name}' would be removed"
        return ret

    try:
        __salt__["rabbitmq_management.policy_delete"](vhost, name, **connection_args)
    except Exception as err:  # pylint: disable=broad-exception-caught
        log.exception("Failed to remove policy '%s' on vhost '%s'", name, vhost)
        ret["result"] = False
        ret["changes"] = {}
        ret["comment"] = f"Failed to remove policy '{name}' on vhost '{vhost}': {err}"
        return ret

    ret["comment"] = f"Policy '{name}' removed"
    return ret
