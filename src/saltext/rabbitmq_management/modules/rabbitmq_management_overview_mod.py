"""RabbitMQ Management API overview and connectivity diagnostics."""

from saltext.rabbitmq_management.modules import rabbitmq_management_mod as _core
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _build_api_url
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _get_management_config
from saltext.rabbitmq_management.modules.rabbitmq_management_mod import _http_request

__virtualname__ = "rabbitmq_management"


def __virtual__():
    return _core.__virtual__()


def test_management_api(**config_override):
    """
    Test connection to RabbitMQ Management API.

    CLI Example:

    .. code-block:: bash

        salt '*' rabbitmq_management.test_management_api
    """
    try:
        config = _get_management_config()
        config.update(config_override)
        url = _build_api_url("/api/overview", **config)

        result = _http_request("GET", "/api/overview", **config_override)
        return {
            "connected": True,
            "url": url,
            "rabbitmq_version": result.get("rabbitmq_version", "unknown"),
            "management_version": result.get("management_version", "unknown"),
            "cluster_name": result.get("cluster_name", "unknown"),
        }
    except Exception as exc:  # pylint: disable=broad-exception-caught
        config = _get_management_config()
        config.update(config_override)
        return {
            "connected": False,
            "error": str(exc),
            "attempted_url": f"{config['scheme']}://{config['host']}:{config['port']}/api/overview",
            "config": {
                "host": config["host"],
                "port": config["port"],
                "user": config["user"],
            },
        }
