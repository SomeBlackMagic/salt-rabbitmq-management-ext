# Managing RabbitMQ shovels

The `rabbitmq_management.shovel_present` and `rabbitmq_management.shovel_absent`
states manage RabbitMQ shovels through the Management API.

## Connection configuration

Configure the Management API connection in the minion configuration or pillar:

```yaml
rabbitmq:
  management:
    config:
      host: rabbitmq.example.com
      port: 15672
      user: salt
      password: secret
      scheme: http
      timeout: 30
```

The RabbitMQ management plugin must be enabled and the configured user must
have administrator permissions to manage shovels.

Connection settings can also be overridden in an individual state.

## What a shovel is

A RabbitMQ shovel moves messages from a source queue on one broker to a
destination queue on another (or the same) broker. Shovels are configured as
runtime parameters and start automatically when the broker restarts.

## Prerequisites

The `rabbitmq_shovel` plugin must be enabled before any shovel can be created:

```bash
rabbitmq-plugins enable rabbitmq_shovel
rabbitmq-plugins enable rabbitmq_shovel_management
```

## Basic inter-broker shovel

Use `shovel_present` to move messages from a queue on one cluster to a queue
on another:

```yaml
migrate_orders:
  rabbitmq_management.shovel_present:
    - name: orders-migration
    - vhost: /
    - src_uri: amqp://user:pass@old-cluster.internal
    - src_queue: orders
    - dest_uri: amqp://user:pass@new-cluster.internal
    - dest_queue: orders
```

When the shovel already exists and its configuration matches, no change is
made. When any parameter differs, the shovel is updated in place.

## Intra-broker shovel

Use `amqp://` (localhost) as both source and destination URIs to move messages
between queues on the same broker:

```yaml
move_to_archive:
  rabbitmq_management.shovel_present:
    - name: archive-shovel
    - vhost: /
    - src_uri: amqp://
    - src_queue: incoming
    - dest_uri: amqp://
    - dest_queue: archive
    - ack_mode: on-confirm
```

## Ack mode

The `ack_mode` parameter controls how the shovel acknowledges messages on the
source queue:

- `on-confirm` (safest) — the message is acknowledged on the source only after
  the destination broker confirms receipt. Guarantees at-least-once delivery.
- `on-publish` — the message is acknowledged as soon as it is published to the
  destination, without waiting for confirmation.
- `no-ack` — messages are consumed without acknowledgement. Highest throughput
  but may lose messages if the destination is unavailable.

```yaml
safe_shovel:
  rabbitmq_management.shovel_present:
    - name: safe-migration
    - vhost: /production
    - src_uri: amqp://old.internal
    - src_queue: events
    - dest_uri: amqp://new.internal
    - dest_queue: events
    - ack_mode: on-confirm
    - prefetch_count: 500
    - reconnect_delay: 5
```

## Source delete policy

The `src_delete_after` parameter controls when messages are deleted from the
source queue:

- `never` (default) — the source queue is not deleted; the shovel runs
  continuously until stopped.
- `queue-length` — the shovel moves exactly the number of messages present in
  the source queue at startup, then stops.

```yaml
drain_and_stop:
  rabbitmq_management.shovel_present:
    - name: drain-temp
    - vhost: /staging
    - src_uri: amqp://
    - src_queue: temp-queue
    - dest_uri: amqp://
    - dest_queue: archive-queue
    - src_delete_after: queue-length
```

## Removing a shovel

Use `shovel_absent` to ensure a shovel does not exist:

```yaml
stop_migration_shovel:
  rabbitmq_management.shovel_absent:
    - name: orders-migration
    - vhost: /
```

The state succeeds without changes when the shovel is already absent.

## Test mode

Salt test mode reports the predicted change without creating or modifying a shovel:

```bash
salt '*' state.apply rabbitmq_shovels test=True
```

When a change is required, the state returns `result: null` and describes the
predicted change in `changes`. If the desired state is already satisfied, it
returns `result: true` with an empty `changes` mapping.

## State parameters

### `shovel_present`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Shovel name. |
| `vhost` | yes | — | RabbitMQ virtual host. |
| `src_uri` | yes | — | AMQP URI of the source broker. Use `amqp://` for localhost. |
| `src_queue` | yes | — | Source queue name. |
| `dest_uri` | yes | — | AMQP URI of the destination broker. Use `amqp://` for localhost. |
| `dest_queue` | yes | — | Destination queue name. |
| `prefetch_count` | no | unmanaged | Maximum number of unacknowledged messages in flight. |
| `reconnect_delay` | no | unmanaged | Seconds to wait before reconnecting after a failure. |
| `ack_mode` | no | unmanaged | Acknowledgement mode: `on-confirm`, `on-publish`, or `no-ack`. |
| `src_delete_after` | no | unmanaged | When to stop the shovel: `never` or `queue-length`. |

Additional keyword arguments are treated as Management API connection overrides
and are passed to every execution-module call made by the state.

### `shovel_absent`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Shovel name. |
| `vhost` | yes | — | RabbitMQ virtual host. |

Additional keyword arguments are treated as Management API connection overrides.
