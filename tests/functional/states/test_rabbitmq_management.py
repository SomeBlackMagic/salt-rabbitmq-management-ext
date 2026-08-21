"""Functional tests for rabbitmq_management state functions.

Idempotency and lifecycle tests for vhost, user, queue, exchange, and policy
states.

The ``mock_http`` fixture (defined in ``tests/functional/conftest.py``) patches
``salt.utils.http.query`` and the private ``_get_management_config`` helper so
no real broker is required.

Notes on HTTP mock patterns
---------------------------
*Not found* — return ``{"status": 200, "body": "null"}`` for states that call
the execution module *directly* via ``user_get`` / ``queue_get``.  Those
helpers check ``if "404" in str(exc)`` to distinguish 404 from other errors,
but ``_http_request`` raises with the message
``"RabbitMQ API endpoint not found: …"`` (no literal "404" in the string), so
the helpers re-raise on 404.  To avoid this edge-case in state logic tests, a
``null`` JSON body tells the execution module that the resource is absent.

For states that route through ``vhost_exist`` / ``user_exist`` (which catch
*all* ``CommandExecutionError``), a ``{"status": 404}`` response is also valid
because the existence-check function returns ``False`` on any error.
"""

import pytest

pytestmark = [
    pytest.mark.requires_salt_states(
        "rabbitmq_management.vhost_present",
        "rabbitmq_management.vhost_absent",
        "rabbitmq_management.user_present",
        "rabbitmq_management.user_absent",
        "rabbitmq_management.queue_present",
        "rabbitmq_management.queue_absent",
        "rabbitmq_management.exchange_present",
        "rabbitmq_management.exchange_absent",
        "rabbitmq_management.policy_present",
        "rabbitmq_management.policy_absent",
    ),
]

# ---------------------------------------------------------------------------
# Shared response helpers
# ---------------------------------------------------------------------------

_VHOST_BODY = '{"name": "/test", "description": "", "tags": [], "tracing": false}'
_USER_BODY = (
    '{"name": "alice", "tags": [], "password_hash": "",'
    ' "hashing_algorithm": "rabbit_password_hashing_sha256"}'
)
_QUEUE_BODY = (
    '{"name": "test-queue", "vhost": "/", "durable": true,'
    ' "auto_delete": false, "arguments": {}}'
)
_EXCHANGE_BODY = (
    '{"name": "test-exchange", "vhost": "/", "type": "direct",'
    ' "durable": true, "auto_delete": false, "internal": false, "arguments": {}}'
)
_POLICY_BODY = (
    '{"name": "test-policy", "vhost": "/", "pattern": ".*",'
    ' "definition": {"ha-mode": "all"}, "priority": 0, "apply-to": "all"}'
)


def _ok(body):
    return {"status": 200, "body": body}


def _null():
    """Simulate a resource that does not exist (execution module returns None)."""
    return {"status": 200, "body": "null"}


def _created():
    return {"status": 201}


def _deleted():
    return {"status": 204}


# ===========================================================================
# vhost
# ===========================================================================


def test_vhost_present_creates(states, mock_http):
    """vhost_present creates a missing vhost and reports result=True with changes."""
    # vhost_exist → vhost_get → GET → 404 → raises → vhost_exist catches → False
    # vhost_create → PUT → 201
    mock_http.side_effect = [{"status": 404}, _created()]

    ret = states.rabbitmq_management.vhost_present(name="/test")

    assert ret.result is True
    assert "created" in ret.comment
    assert ret.changes != {}


def test_vhost_present_idempotent(states, mock_http):
    """vhost_present returns result=True with no changes when vhost already matches."""
    # vhost_exist → vhost_get → GET → 200 (exists)
    # state calls vhost_get again → GET → 200
    mock_http.side_effect = [_ok(_VHOST_BODY), _ok(_VHOST_BODY)]

    ret = states.rabbitmq_management.vhost_present(name="/test")

    assert ret.result is True
    assert ret.changes == {}


def test_vhost_absent_removes(states, mock_http):
    """vhost_absent removes an existing vhost."""
    # vhost_exist → vhost_get → GET → 200 (exists)
    # vhost_delete → DELETE → 204
    mock_http.side_effect = [_ok(_VHOST_BODY), _deleted()]

    ret = states.rabbitmq_management.vhost_absent(name="/test")

    assert ret.result is True
    assert ret.changes != {}
    assert "removed" in ret.comment


def test_vhost_absent_already_absent(states, mock_http):
    """vhost_absent returns result=True with no changes when vhost does not exist."""
    # vhost_exist → vhost_get → GET → 404 → raises → vhost_exist catches → False
    mock_http.side_effect = [{"status": 404}]

    ret = states.rabbitmq_management.vhost_absent(name="/nonexistent")

    assert ret.result is True
    assert ret.changes == {}
    assert "absent" in ret.comment


def test_vhost_present_test_mode(states, mock_http):
    """vhost_present returns result=None in test mode when vhost does not exist."""
    mock_http.side_effect = [{"status": 404}]

    ret = states.rabbitmq_management.vhost_present(name="/test", test=True)

    assert ret.result is None
    assert ret.changes != {}


# ===========================================================================
# user
# ===========================================================================


def test_user_present_creates(states, mock_http):
    """user_present creates a missing user and reports result=True with changes."""
    # user_get → GET → null → returns None → user does not exist
    # user_create → PUT → 201
    mock_http.side_effect = [_null(), _created()]

    ret = states.rabbitmq_management.user_present(name="alice")

    assert ret.result is True
    assert "created" in ret.comment
    assert ret.changes != {}


def test_user_present_idempotent(states, mock_http):
    """user_present returns result=True with no changes when user already matches."""
    # user_get → GET → 200 (exists, same tags=[], no password managed)
    mock_http.side_effect = [_ok(_USER_BODY)]

    ret = states.rabbitmq_management.user_present(name="alice")

    assert ret.result is True
    assert ret.changes == {}


def test_user_absent_removes(states, mock_http):
    """user_absent removes an existing user."""
    # user_exist → user_get → GET → 200 (exists)
    # user_delete → DELETE → 204
    mock_http.side_effect = [_ok(_USER_BODY), _deleted()]

    ret = states.rabbitmq_management.user_absent(name="alice")

    assert ret.result is True
    assert ret.changes != {}


def test_user_absent_already_absent(states, mock_http):
    """user_absent returns result=True with no changes when user does not exist."""
    # user_exist → user_get → GET → 404 → raises → user_exist catches → False
    mock_http.side_effect = [{"status": 404}]

    ret = states.rabbitmq_management.user_absent(name="alice")

    assert ret.result is True
    assert ret.changes == {}


# ===========================================================================
# queue
# ===========================================================================


def test_queue_present_creates(states, mock_http):
    """queue_present creates a missing queue."""
    # queue_get → GET → null → returns None
    # queue_create → PUT → 201
    mock_http.side_effect = [_null(), _created()]

    ret = states.rabbitmq_management.queue_present(name="test-queue", vhost="/")

    assert ret.result is True
    assert "created" in ret.comment
    assert ret.changes != {}


def test_queue_present_idempotent(states, mock_http):
    """queue_present returns result=True with no changes when queue matches."""
    # queue_get → GET → 200 (exists, matching params)
    mock_http.side_effect = [_ok(_QUEUE_BODY)]

    ret = states.rabbitmq_management.queue_present(
        name="test-queue", vhost="/", durable=True, auto_delete=False
    )

    assert ret.result is True
    assert ret.changes == {}


def test_queue_absent_removes(states, mock_http):
    """queue_absent removes an existing queue."""
    # queue_exist → queue_get → GET → 200 (exists)
    # queue_delete → DELETE → 204
    mock_http.side_effect = [_ok(_QUEUE_BODY), _deleted()]

    ret = states.rabbitmq_management.queue_absent(name="test-queue", vhost="/")

    assert ret.result is True
    assert ret.changes != {}


def test_queue_absent_already_absent(states, mock_http):
    """queue_absent returns result=True with no changes when queue does not exist."""
    # queue_exist → queue_get → GET → 404 → raises → queue_exist catches → False
    mock_http.side_effect = [{"status": 404}]

    ret = states.rabbitmq_management.queue_absent(name="test-queue", vhost="/")

    assert ret.result is True
    assert ret.changes == {}


# ===========================================================================
# exchange
# ===========================================================================


def test_exchange_present_creates(states, mock_http):
    """exchange_present creates a missing exchange."""
    mock_http.side_effect = [_null(), _created()]

    ret = states.rabbitmq_management.exchange_present(
        name="test-exchange", vhost="/", type="direct"
    )

    assert ret.result is True
    assert ret.changes != {}


def test_exchange_present_idempotent(states, mock_http):
    """exchange_present returns result=True with no changes when exchange matches."""
    mock_http.side_effect = [_ok(_EXCHANGE_BODY)]

    ret = states.rabbitmq_management.exchange_present(
        name="test-exchange", vhost="/", type="direct", durable=True
    )

    assert ret.result is True
    assert ret.changes == {}


def test_exchange_absent_already_absent(states, mock_http):
    """exchange_absent returns result=True with no changes when exchange does not exist."""
    mock_http.side_effect = [{"status": 404}]

    ret = states.rabbitmq_management.exchange_absent(name="test-exchange", vhost="/")

    assert ret.result is True
    assert ret.changes == {}


# ===========================================================================
# policy
# ===========================================================================


def test_policy_present_creates(states, mock_http):
    """policy_present creates a missing policy."""
    mock_http.side_effect = [_null(), _created()]

    ret = states.rabbitmq_management.policy_present(
        name="test-policy",
        vhost="/",
        pattern=".*",
        definition={"ha-mode": "all"},
    )

    assert ret.result is True
    assert ret.changes != {}


def test_policy_present_idempotent(states, mock_http):
    """policy_present returns result=True with no changes when policy matches."""
    mock_http.side_effect = [_ok(_POLICY_BODY)]

    ret = states.rabbitmq_management.policy_present(
        name="test-policy",
        vhost="/",
        pattern=".*",
        definition={"ha-mode": "all"},
        priority=0,
        apply_to="all",
    )

    assert ret.result is True
    assert ret.changes == {}


def test_policy_absent_already_absent(states, mock_http):
    """policy_absent returns result=True with no changes when policy does not exist."""
    mock_http.side_effect = [{"status": 404}]

    ret = states.rabbitmq_management.policy_absent(name="test-policy", vhost="/")

    assert ret.result is True
    assert ret.changes == {}
