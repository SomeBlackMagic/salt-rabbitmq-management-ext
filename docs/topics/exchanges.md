# Managing RabbitMQ exchanges

The `rabbitmq_management.exchange_present` and
`rabbitmq_management.exchange_absent` states manage RabbitMQ exchanges through
the Management API.

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
have permission to manage exchanges in the selected virtual host.

Connection settings can also be overridden in an individual state.

## Creating an exchange

Use `exchange_present` to ensure an exchange exists with the desired configuration:

```yaml
orders_exchange:
  rabbitmq_management.exchange_present:
    - name: orders
    - vhost: /production
    - type: topic
    - durable: true
```

When the exchange already exists and its configuration matches, no change is
made. Applying the state again is safe and produces no output.

## Exchange types

RabbitMQ supports four exchange types:

- `direct` (default) — routes messages to queues whose binding key exactly
  matches the routing key
- `fanout` — routes messages to all bound queues, ignoring the routing key
- `topic` — routes messages based on wildcard pattern matching on the routing key
- `headers` — routes messages based on message header attributes

```yaml
events_fanout:
  rabbitmq_management.exchange_present:
    - name: events
    - vhost: /
    - type: fanout
    - durable: true

notifications_topic:
  rabbitmq_management.exchange_present:
    - name: notifications
    - vhost: /
    - type: topic
    - durable: true
```

## Internal exchange

An internal exchange is not accessible by clients directly. It can only receive
messages from other exchanges via exchange-to-exchange bindings. Use it to
build routing topologies that are invisible to publishers:

```yaml
internal_router:
  rabbitmq_management.exchange_present:
    - name: internal-router
    - vhost: /
    - type: direct
    - durable: true
    - internal: true
```

## Built-in exchanges

RabbitMQ reserves exchanges whose names start with `amq.` (such as
`amq.direct`, `amq.fanout`, `amq.topic`). The state will fail if you attempt
to create, modify, or remove a built-in exchange:

```
Exchange 'amq.direct' is a built-in RabbitMQ exchange (amq.*) and cannot be recreated.
```

## Immutable parameters

RabbitMQ does not allow modifying `type`, `durable`, `auto_delete`, or
`internal` on an existing exchange. When these parameters differ from the
current configuration, the state fails by default:

```
Exchange 'orders' exists with different parameters. Use force=True to recreate it.
```

Set `force: true` to delete and recreate the exchange. All bindings to the
exchange are lost when it is recreated.

```yaml
orders_exchange:
  rabbitmq_management.exchange_present:
    - name: orders
    - vhost: /production
    - type: fanout
    - durable: true
    - force: true
```

`force: true` has no effect on built-in exchanges. The state fails regardless.

## Removing an exchange

Use `exchange_absent` to ensure an exchange does not exist:

```yaml
remove_legacy_exchange:
  rabbitmq_management.exchange_absent:
    - name: legacy-orders
    - vhost: /
```

The state succeeds without changes when the exchange is already absent.

## Conditional delete

Use `if_unused` to prevent removal of an exchange that still has queue bindings:

```yaml
safe_remove_exchange:
  rabbitmq_management.exchange_absent:
    - name: old-events
    - vhost: /
    - if_unused: true
```

RabbitMQ returns an error when the exchange is still in use. The state
propagates this error and marks the run as failed.

## Test mode

Salt test mode reports the predicted change without creating or deleting an exchange:

```bash
salt '*' state.apply rabbitmq_exchanges test=True
```

When a change is required, the state returns `result: null` and describes the
predicted change in `changes`. If the desired state is already satisfied, it
returns `result: true` with an empty `changes` mapping.

## State parameters

### `exchange_present`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Exchange name. |
| `vhost` | no | `/` | RabbitMQ virtual host. |
| `type` | no | `direct` | Exchange type: `direct`, `fanout`, `topic`, or `headers`. |
| `durable` | no | `true` | Survive broker restart. |
| `auto_delete` | no | `false` | Delete when the last queue binding is removed. |
| `internal` | no | `false` | Not directly accessible by clients; only usable via exchange-to-exchange bindings. |
| `arguments` | no | `{}` | Exchange arguments as a mapping or JSON string. |
| `force` | no | `false` | Delete and recreate the exchange when immutable parameters differ. All bindings are lost. |

Additional keyword arguments are treated as Management API connection overrides
and are passed to every execution-module call made by the state.

### `exchange_absent`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Exchange name. |
| `vhost` | no | `/` | RabbitMQ virtual host. |
| `if_unused` | no | `false` | Only delete the exchange when no queues are bound to it. |

Additional keyword arguments are treated as Management API connection overrides.
