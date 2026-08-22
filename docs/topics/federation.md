# Managing RabbitMQ federation

The `rabbitmq_management.federation_upstream_present` and
`rabbitmq_management.federation_upstream_absent` states manage RabbitMQ
federation upstreams through the Management API.

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
have administrator permissions to manage federation upstreams.

Connection settings can also be overridden in an individual state.

## What federation is

RabbitMQ federation links exchanges or queues across separate brokers so that
messages published on one broker flow to consumers on another. A federation
upstream defines the remote broker connection and the parameters of the link.

## Prerequisites

The `rabbitmq_federation` plugin must be enabled on the broker before any
upstream can be created:

```bash
rabbitmq-plugins enable rabbitmq_federation
rabbitmq-plugins enable rabbitmq_federation_management
```

## Creating an upstream

Use `federation_upstream_present` to ensure an upstream exists:

```yaml
remote_dc_upstream:
  rabbitmq_management.federation_upstream_present:
    - name: remote-dc
    - vhost: /
    - uri: amqp://rabbit@remote-dc.internal
```

When the upstream already exists and its configuration matches, no change is
made. When any parameter differs, the upstream is updated in place.

## High-availability upstream

Supply a list of URIs to connect to any available node in a remote cluster:

```yaml
ha_upstream:
  rabbitmq_management.federation_upstream_present:
    - name: ha-upstream
    - vhost: /production
    - uri:
      - amqp://node1.rabbit.internal
      - amqp://node2.rabbit.internal
    - reconnect_delay: 5
    - ack_mode: on-confirm
```

## Queue federation vs exchange federation

By default, federation federates exchanges. To federate a specific queue
instead, set the `queue` parameter:

```yaml
queue_upstream:
  rabbitmq_management.federation_upstream_present:
    - name: orders-queue-upstream
    - vhost: /
    - uri: amqp://remote.internal
    - queue: orders
```

To federate a specific exchange, set the `exchange` parameter:

```yaml
exchange_upstream:
  rabbitmq_management.federation_upstream_present:
    - name: events-exchange-upstream
    - vhost: /
    - uri: amqp://remote.internal
    - exchange: events
```

## Tuning the upstream link

Control prefetch, reconnect delay, and acknowledgement behaviour:

```yaml
tuned_upstream:
  rabbitmq_management.federation_upstream_present:
    - name: tuned-upstream
    - vhost: /production
    - uri: amqp://remote.internal
    - prefetch_count: 1000
    - reconnect_delay: 10
    - ack_mode: on-confirm
    - max_hops: 2
```

`ack_mode` accepts three values:

- `on-confirm` (recommended) — message is removed from the upstream queue only
  after the downstream broker confirms it
- `on-publish` — message is removed as soon as it is published downstream
- `no-ack` — no acknowledgement; highest throughput but may lose messages

## TTL and expiry

Set `expires` to automatically close an idle upstream link after a period of
inactivity (in milliseconds). Set `message_ttl` to limit how long messages
survive on the upstream link queue:

```yaml
expiring_upstream:
  rabbitmq_management.federation_upstream_present:
    - name: temp-upstream
    - vhost: /staging
    - uri: amqp://staging-remote.internal
    - expires: 3600000
    - message_ttl: 60000
```

## Removing an upstream

Use `federation_upstream_absent` to ensure an upstream does not exist:

```yaml
remove_old_upstream:
  rabbitmq_management.federation_upstream_absent:
    - name: legacy-dc
    - vhost: /
```

The state succeeds without changes when the upstream is already absent.

## Test mode

Salt test mode reports the predicted change without creating or modifying an upstream:

```bash
salt '*' state.apply rabbitmq_federation test=True
```

When a change is required, the state returns `result: null` and describes the
predicted change in `changes`. If the desired state is already satisfied, it
returns `result: true` with an empty `changes` mapping.

## State parameters

### `federation_upstream_present`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Upstream name. |
| `vhost` | yes | — | RabbitMQ virtual host. |
| `uri` | yes | — | AMQP URI(s) of the upstream broker. Accepts a string or a list of strings. |
| `expires` | no | unmanaged | Upstream link expiry in milliseconds. Removes the upstream link when idle. |
| `message_ttl` | no | unmanaged | Message TTL in milliseconds on the upstream link queue. |
| `max_hops` | no | unmanaged | Maximum number of federation hops for a message. |
| `prefetch_count` | no | unmanaged | Maximum number of unacknowledged messages on the link. |
| `reconnect_delay` | no | unmanaged | Seconds to wait before reconnecting after a failure. |
| `ack_mode` | no | unmanaged | Acknowledgement mode: `on-confirm`, `on-publish`, or `no-ack`. |
| `trust_user_id` | no | unmanaged | When `true`, the upstream user-id property is trusted and forwarded. |
| `exchange` | no | unmanaged | Upstream exchange to federate. Omit to federate all exchanges matched by the policy. |
| `queue` | no | unmanaged | Upstream queue to federate. Mutually exclusive with `exchange`. |

Additional keyword arguments are treated as Management API connection overrides
and are passed to every execution-module call made by the state.

### `federation_upstream_absent`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Upstream name. |
| `vhost` | yes | — | RabbitMQ virtual host. |

Additional keyword arguments are treated as Management API connection overrides.
