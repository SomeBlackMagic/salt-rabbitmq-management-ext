The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

This project uses [Semantic Versioning](https://semver.org/) - MAJOR.MINOR.PATCH

# Changelog

## 0.1.0 (2026-08-22)


### Fixed

- Fix HTTP 404 error detection in ``_http_request`` (message now includes the status code) and add missing ``CommandExecutionError`` handling in ``user_exist``, ``queue_exist``, ``exchange_exist``, and ``policy_exist`` so they return ``False`` instead of propagating the exception when a resource is not found.


### Added

- Add idempotent states for managing RabbitMQ queue and exchange bindings. [#0](https://github.com/SomeBlackMagic/salt-rabbitmq-management-ext/issues/0)
- Add functional tests for execution modules and state idempotency (vhost, user, queue, exchange, policy) using mocked HTTP, and integration tests against a live RabbitMQ container via Docker Compose.
- Add idempotent states for creating and removing RabbitMQ exchanges, with conflict detection, force-recreate support, and built-in exchange protection.
- Add idempotent states for creating, updating, and removing RabbitMQ federation upstreams, with support for all upstream parameters including URI lists, TTL, prefetch count, ack mode, and reconnect delay.
- Add idempotent states for creating, updating, and removing RabbitMQ policies, with support for pattern, definition (dict or JSON string), priority, and apply-to configuration.
- Add idempotent states for creating, updating, and removing RabbitMQ runtime parameters, with support for arbitrary component types (federation-upstream, shovel, etc.) and JSON string value normalization.
- Add idempotent states for creating, updating, and removing RabbitMQ shovels, with support for all shovel parameters including source/destination URIs, queue names, prefetch count, ack mode, reconnect delay, and source delete-after policy.
- Add idempotent states for creating, updating, and removing RabbitMQ users, including passwords sourced from Salt SDB.
- Add idempotent states for creating, updating, and removing RabbitMQ virtual hosts, with support for description, tags, default queue type, and tracing configuration.
- Add idempotent states for setting and removing RabbitMQ user limits (max-connections, max-channels) via ``user_limit_present`` and ``user_limit_absent``.
- Add idempotent states for setting and removing RabbitMQ user permissions on virtual hosts, including configure, write, and read regex fields and Salt test-mode support.
- Add idempotent states for setting and removing RabbitMQ virtual host limits (max-connections, max-queues) via ``vhost_limit_present`` and ``vhost_limit_absent``.
