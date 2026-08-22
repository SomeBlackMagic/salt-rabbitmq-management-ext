"""
Module to provide RabbitMQ compatibility to Salt.

This module manages RabbitMQ via HTTP Management API.

Configuration:
    rabbitmq:
      management:
        config:
          host: localhost
          port: 15672
          user: guest
          password: guest
          scheme: http
          timeout: 30
"""

import base64
import logging

import salt.utils.http
import salt.utils.json
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

__virtualname__ = "rabbitmq_management"
__salt__ = {}


def __virtual__():
    """
    Only load this module if salt.utils.http is available.
    This module uses RabbitMQ HTTP Management API and doesn't require rabbitmqctl.
    """
    return __virtualname__


# =============================================================================
# HTTP Management API Infrastructure
# =============================================================================


def _get_management_config():
    """
    Get RabbitMQ Management API configuration from pillar/config.

    Returns dict with connection parameters.
    """
    config = {}
    if "config.option" in __salt__:
        rabbitmq_config = __salt__["config.option"]("rabbitmq", {})
        management_config = rabbitmq_config.get("management", {})
        config = management_config.get("config", {})

    return {
        "host": config.get("host", "localhost"),
        "port": config.get("port", 15672),
        "user": config.get("user", "guest"),
        "password": config.get("password", "guest"),
        "scheme": config.get("scheme", "http"),
        "timeout": config.get("timeout", 30),
    }


def _build_api_url(path, **config_override):
    """
    Build full URL for RabbitMQ Management API endpoint.

    Args:
        path: API endpoint path (e.g., '/api/vhosts')
              Path can contain already URL-encoded parts (e.g., %2F for /)
        **config_override: Override default config values

    Returns:
        str: Full URL
    """
    config = _get_management_config()
    config.update(config_override)

    base_url = "{}://{}:{}".format(config["scheme"], config["host"], config["port"])

    # Simple concatenation - path is already properly encoded by calling functions
    # Don't use urljoin as it can mess up already encoded characters
    if not path.startswith("/"):
        path = "/" + path

    return base_url + path


def _http_request(method, path, data=None, **config_override):
    """
    Make HTTP request to RabbitMQ Management API.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API endpoint path
        data: Request body (will be JSON-encoded if dict)
        **config_override: Override default config values

    Returns:
        dict: Response data (parsed JSON) or dict with status/error

    Raises:
        CommandExecutionError: On HTTP or connection errors
    """
    config = _get_management_config()
    config.update(config_override)

    url = _build_api_url(path, **config)

    # Prepare authentication
    auth_string = "{}:{}".format(config["user"], config["password"])
    auth_bytes = auth_string.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("ascii")

    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json",
    }

    # Prepare request body
    if data is not None and not isinstance(data, str):
        data = salt.utils.json.dumps(data)

    log.debug("RabbitMQ API request: %s %s", method, url)

    try:
        result = salt.utils.http.query(
            url,
            method=method,
            data=data,
            header_dict=headers,
            decode=False,  # НЕ декодировать автоматически
            status=True,
            timeout=config["timeout"],
        )

        status = result.get("status")

        # Handle different response codes
        if status in [201, 204]:  # Created or No Content (success)
            return {"status": "success"}

        if status == 404:
            raise CommandExecutionError(f"HTTP 404 Not Found: {path}")

        if status >= 400:
            error_msg = result.get("body", result.get("error", "Unknown error"))
            raise CommandExecutionError(f"RabbitMQ API error (HTTP {status}): {error_msg}")

        # Try to parse JSON body for successful responses
        body = result.get("body")
        if body:
            try:
                return salt.utils.json.loads(body)
            except Exception:  # pylint: disable=broad-exception-caught
                return {"body": body}

        return {"status": "success"}

    except ConnectionError as exc:
        raise CommandExecutionError(
            f"Cannot connect to RabbitMQ Management API at {url}: {exc}"
        ) from exc
    except TimeoutError as exc:
        raise CommandExecutionError(
            f"Connection timeout to RabbitMQ Management API at {url}: {exc}"
        ) from exc
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise CommandExecutionError(f"RabbitMQ API request failed: {exc}") from exc
