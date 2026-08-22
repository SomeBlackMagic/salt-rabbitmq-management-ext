# Managing RabbitMQ queues

The `rabbitmq_management.queue_present` and `rabbitmq_management.queue_absent`
states manage RabbitMQ queues through the Management API.

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
have permission to manage queues in the selected virtual host.

Connection settings can also be overridden in an individual state.

## Creating a basic queue

Use `queue_present` to ensure a queue exists with the desired configuration:

```yaml
orders_queue:
  rabbitmq_management.queue_present:
    - name: orders
    - vhost: /production
    - durable: true
```

When the queue already exists and its configuration matches, no change is made.
Applying the state again is safe and produces no output.

## Quorum queue

Create a quorum queue by passing the `x-queue-type` argument:

```yaml
orders_quorum_queue:
  rabbitmq_management.queue_present:
    - name: orders-quorum
    - vhost: /production
    - durable: true
    - arguments:
        x-queue-type: quorum
```

Quorum queues are always durable. Setting `durable: false` with a quorum queue
type will be rejected by RabbitMQ.

## Queue TTL and max-length

Use `x-message-ttl` and `x-max-length` arguments to control queue behaviour:

```yaml
temp_orders_queue:
  rabbitmq_management.queue_present:
    - name: temp-orders
    - vhost: /staging
    - durable: true
    - arguments:
        x-message-ttl: 3600000
        x-max-length: 10000
```

Arguments can also be supplied as a JSON string:

```yaml
    - arguments: '{"x-message-ttl": 3600000, "x-max-length": 10000}'
```

## Immutable parameters

RabbitMQ does not allow modifying `durable`, `auto_delete`, or `arguments` on
an existing queue. When these parameters differ from the current configuration,
the state fails by default:

```
Queue 'orders' exists with different parameters. Use force=True to recreate it.
```

Set `force: true` to delete and recreate the queue. **This is a destructive
operation that discards all messages currently in the queue.**

```yaml
orders_queue:
  rabbitmq_management.queue_present:
    - name: orders
    - vhost: /production
    - durable: true
    - arguments:
        x-queue-type: quorum
    - force: true
```

## Removing a queue

Use `queue_absent` to ensure a queue does not exist:

```yaml
remove_temp_queue:
  rabbitmq_management.queue_absent:
    - name: temp-processing
    - vhost: /staging
```

The state succeeds without changes when the queue is already absent.

## Conditional delete

Use `if_empty` or `if_unused` to prevent accidental removal of active queues:

```yaml
safe_remove_queue:
  rabbitmq_management.queue_absent:
    - name: temp-processing
    - vhost: /staging
    - if_empty: true
    - if_unused: true
```

RabbitMQ returns an error when the condition is not met. The state propagates
this error and marks the run as failed.

## Test mode

Salt test mode reports the predicted change without creating or deleting a queue:

```bash
salt '*' state.apply rabbitmq_queues test=True
```

When a change is required, the state returns `result: null` and describes the
predicted change in `changes`. If the desired state is already satisfied, it
returns `result: true` with an empty `changes` mapping.

## State parameters

### `queue_present`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Queue name. |
| `vhost` | no | `/` | RabbitMQ virtual host. |
| `durable` | no | `true` | Survive broker restart. |
| `auto_delete` | no | `false` | Delete when last consumer disconnects. |
| `arguments` | no | `{}` | Queue arguments as a mapping or JSON string (e.g. `x-queue-type`, `x-message-ttl`, `x-max-length`). |
| `force` | no | `false` | Delete and recreate the queue when immutable parameters differ. Discards all messages. |

Additional keyword arguments are treated as Management API connection overrides
and are passed to every execution-module call made by the state.

### `queue_absent`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Queue name. |
| `vhost` | no | `/` | RabbitMQ virtual host. |
| `if_empty` | no | `false` | Only delete the queue when it contains no messages. |
| `if_unused` | no | `false` | Only delete the queue when it has no consumers. |

Additional keyword arguments are treated as Management API connection overrides.
