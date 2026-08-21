from unittest.mock import Mock

import pytest

from saltext.rabbitmq_management.modules import rabbitmq_management_binding_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_exchange_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_federation_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_limit_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_overview_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_parameter_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_permission_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_policy_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_queue_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_shovel_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_user_mod
from saltext.rabbitmq_management.modules import rabbitmq_management_vhost_mod

DOMAIN_MODULES = (
    rabbitmq_management_binding_mod,
    rabbitmq_management_exchange_mod,
    rabbitmq_management_federation_mod,
    rabbitmq_management_limit_mod,
    rabbitmq_management_overview_mod,
    rabbitmq_management_parameter_mod,
    rabbitmq_management_permission_mod,
    rabbitmq_management_policy_mod,
    rabbitmq_management_queue_mod,
    rabbitmq_management_shovel_mod,
    rabbitmq_management_user_mod,
    rabbitmq_management_vhost_mod,
)


def test_execution_modules_share_virtual_name():
    for module in (rabbitmq_management_mod, *DOMAIN_MODULES):
        assert module.__virtualname__ == "rabbitmq_management"


@pytest.mark.parametrize("module", DOMAIN_MODULES)
def test_domain_virtual_delegates_to_core(module, monkeypatch):
    virtual = Mock(return_value="rabbitmq_management")
    monkeypatch.setattr(rabbitmq_management_mod, "__virtual__", virtual)

    assert module.__virtual__() == "rabbitmq_management"
    virtual.assert_called_once_with()


def test_vhost_list_delegates_to_shared_http_request(monkeypatch):
    request = Mock(return_value=[{"name": "/"}])
    monkeypatch.setattr(rabbitmq_management_vhost_mod, "_http_request", request)

    assert rabbitmq_management_vhost_mod.vhost_list(timeout=10) == [{"name": "/"}]
    request.assert_called_once_with("GET", "/api/vhosts", timeout=10)


def test_vhost_create_sends_explicit_empty_values(monkeypatch):
    request = Mock(return_value={"status": "success"})
    monkeypatch.setattr(rabbitmq_management_vhost_mod, "_http_request", request)

    result = rabbitmq_management_vhost_mod.vhost_create("/", description="", tags=[])

    assert result == {"status": "created", "name": "/"}
    request.assert_called_once_with(
        "PUT",
        "/api/vhosts/%2F",
        data={"tracing": False, "description": "", "tags": []},
    )


def test_management_api_uses_overview_endpoint(monkeypatch):
    monkeypatch.setattr(
        rabbitmq_management_overview_mod,
        "_get_management_config",
        Mock(return_value={"scheme": "https", "host": "rabbit", "port": 15671}),
    )
    monkeypatch.setattr(
        rabbitmq_management_overview_mod,
        "_build_api_url",
        Mock(return_value="https://rabbit:15671/api/overview"),
    )
    request = Mock(
        return_value={
            "rabbitmq_version": "4.1.0",
            "management_version": "4.1.0",
            "cluster_name": "rabbit@node",
        }
    )
    monkeypatch.setattr(rabbitmq_management_overview_mod, "_http_request", request)

    assert rabbitmq_management_overview_mod.test_management_api(timeout=10) == {
        "connected": True,
        "url": "https://rabbit:15671/api/overview",
        "rabbitmq_version": "4.1.0",
        "management_version": "4.1.0",
        "cluster_name": "rabbit@node",
    }
    request.assert_called_once_with("GET", "/api/overview", timeout=10)


def test_federation_create_delegates_to_parameter_module(monkeypatch):
    create = Mock(return_value={"status": "created"})
    monkeypatch.setattr(rabbitmq_management_federation_mod, "_parameter_create", create)

    result = rabbitmq_management_federation_mod.federation_upstream_create(
        "/",
        "remote",
        "amqp://remote",
        expires=3600,
        prefetch_count=100,
        timeout=10,
    )

    assert result == {"status": "created"}
    create.assert_called_once_with(
        "federation-upstream",
        "/",
        "remote",
        {
            "uri": "amqp://remote",
            "expires": 3600,
            "prefetch-count": 100,
        },
        timeout=10,
    )
