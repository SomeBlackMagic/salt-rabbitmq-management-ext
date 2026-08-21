"""RabbitMQ policy management via the Management API."""

from urllib.parse import quote

import salt.utils.json
from salt.exceptions import CommandExecutionError

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _http_request

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


# =============================================================================
# Policies Management (HTTP API)
# =============================================================================


def policy_list(vhost="/", **config_override):
    """
    List all policies in a vhost.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.policy_list
        salt '*' rabbitmq_management.policy_list /production

    Args:
        vhost: Virtual host name (default: /)

    Returns:
        list: List of dicts with policy information
    """
    path = f"/api/policies/{quote(vhost, safe='')}"
    return _http_request("GET", path, **config_override)


def policy_get(vhost, name, **config_override):
    """
    Get information about a specific policy.

    CLI Examples:

    .. code-block:: bash

        salt '*' rabbitmq_management.policy_get / ha-policy
        salt '*' rabbitmq_management.policy_get /production mirror-policy

    Args:
        vhost: Virtual host name
        name: Policy name

    Returns:
        dict: Policy details or None if not found
    """
    try:
        path = f"/api/policies/{quote(vhost, safe='')}/{quote(name, safe='')}"
        return _http_request("GET", path, **config_override)
    except CommandExecutionError as exc:
        if "404" in str(exc):
            return None
        raise


def policy_create(vhost, name, pattern, definition, priority=0, apply_to="all", **config_override):
    """
    Create or update a policy.

    CLI Examples:

    .. code-block:: bash

        # HA policy (mirror all queues)
        salt '*' rabbitmq_management.policy_create / ha-all '^.*' '{"ha-mode":"all"}'

        # HA policy (mirror to 2 nodes)
        salt '*' rabbitmq_management.policy_create / ha-two '^ha\\.' '{"ha-mode":"exactly","ha-params":2}'

        # Message TTL policy
        salt '*' rabbitmq_management.policy_create / ttl '^temp\\.' '{"message-ttl":60000}'

        # Max length policy
        salt '*' rabbitmq_management.policy_create / limited '^limited\\.' '{"max-length":1000}'

        # Apply only to queues
        salt '*' rabbitmq_management.policy_create / queue-policy '^.*' '{"ha-mode":"all"}' apply_to=queues

        # Apply only to exchanges
        salt '*' rabbitmq_management.policy_create / ex-policy '^.*' '{"alternate-exchange":"backup"}' apply_to=exchanges

        # With priority (higher number = higher priority)
        salt '*' rabbitmq_management.policy_create / priority-policy '^important\\.' '{"ha-mode":"all"}' priority=10

    Args:
        vhost: Virtual host name
        name: Policy name
        pattern: Regex pattern to match queue/exchange names
        definition: Policy definition as dict or JSON string with policy settings
        priority: Policy priority (default: 0, higher number = higher priority)
        apply_to: Apply to: all, queues, exchanges (default: all)

    Common definition keys:
        HA (High Availability):
        - ha-mode: all, exactly, nodes
        - ha-params: number (for exactly) or node names list (for nodes)
        - ha-sync-mode: automatic, manual
        - ha-promote-on-shutdown: when-synced, always
        - ha-promote-on-failure: when-synced, always

        Queue limits:
        - max-length: Maximum queue length
        - max-length-bytes: Maximum queue size in bytes
        - overflow: drop-head, reject-publish, reject-publish-dlx
        - message-ttl: Message TTL in milliseconds
        - expires: Queue expiration time in milliseconds

        Dead letter:
        - dead-letter-exchange: Dead letter exchange name
        - dead-letter-routing-key: Routing key for dead letters

        Federation:
        - federation-upstream-set: Upstream set name

        Other:
        - queue-mode: lazy, default
        - delivery-limit: Max delivery attempts

    Returns:
        dict: Operation result
    """
    data = {
        "pattern": pattern,
        "priority": priority,
        "apply-to": apply_to,
    }

    # Handle definition
    if isinstance(definition, str):
        definition = salt.utils.json.loads(definition)
    data["definition"] = definition

    path = f"/api/policies/{quote(vhost, safe='')}/{quote(name, safe='')}"
    _http_request("PUT", path, data=data, **config_override)

    return {"status": "created", "vhost": vhost, "name": name}


def policy_delete(vhost, name, **config_override):
    """
    Delete a policy.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.policy_delete / ha-policy

    Args:
        vhost: Virtual host name
        name: Policy name

    Returns:
        dict: Operation result
    """
    path = f"/api/policies/{quote(vhost, safe='')}/{quote(name, safe='')}"
    _http_request("DELETE", path, **config_override)

    return {"status": "deleted", "vhost": vhost, "name": name}


def policy_exist(vhost, name, **config_override):
    """
    Check if a policy exists.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.policy_exist / ha-policy

    Args:
        vhost: Virtual host name
        name: Policy name

    Returns:
        bool: True if policy exists, False otherwise
    """
    result = policy_get(vhost, name, **config_override)
    return result is not None
