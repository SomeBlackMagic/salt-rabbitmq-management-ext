# Managing RabbitMQ bindings

The `rabbitmq_management.binding_present` and
`rabbitmq_management.binding_absent` states manage bindings between an exchange
and a queue or between two exchanges through the RabbitMQ Management API.

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
have permission to manage bindings in the selected virtual host.

Connection settings can also be overridden in an individual state. For
example, `timeout: 10` is passed to every Management API call made by that
state.

## Queue bindings

Use `binding_present` with the default `destination_type: queue` to create a
binding from an exchange to a queue:

```yaml
bind_orders_queue:
  rabbitmq_management.binding_present:
    - name: orders-exchange-to-queue
    - vhost: /production
    - source: orders-exchange
    - destination: orders-queue
    - routing_key: new-order
```

The `name` value identifies the Salt state result. It does not identify the
RabbitMQ binding. A binding is matched using `source`, `destination`,
`destination_type`, `routing_key`, and `arguments`.

Applying the state again does not create another binding when the same binding
already exists.

## Exchange-to-exchange bindings

Set `destination_type` to `exchange` when the destination is another exchange:

```yaml
bind_incoming_to_processing:
  rabbitmq_management.binding_present:
    - name: incoming-to-processing
    - vhost: /
    - source: incoming
    - destination: processing
    - destination_type: exchange
    - routing_key: orders.*
```

Only `queue` and `exchange` are accepted as destination types.

## Binding arguments

Binding arguments can be supplied as a YAML mapping. This is commonly used
with a headers exchange:

```yaml
bind_priority_orders:
  rabbitmq_management.binding_present:
    - name: priority-orders
    - vhost: /
    - source: orders-headers
    - destination: priority-orders
    - routing_key: ""
    - arguments:
        x-match: all
        type: order
        priority: high
```

A JSON object string is also accepted:

```yaml
    - arguments: '{"x-match": "all", "type": "order"}'
```

Omitting `arguments`, setting it to `null`, and using an empty mapping are
equivalent:

```yaml
    - arguments: {}
```

Argument values are part of the binding identity. To remove a binding with
arguments, supply the same arguments used to create it.

## Removing a binding

Use `binding_absent` with the same identity fields:

```yaml
remove_legacy_orders_binding:
  rabbitmq_management.binding_absent:
    - name: legacy-orders-binding
    - vhost: /
    - source: old-exchange
    - destination: orders-queue
    - routing_key: orders
```

The state retrieves the binding from RabbitMQ and uses its `properties_key`
when deleting it. This is important for bindings with arguments, because their
`properties_key` may be a RabbitMQ-generated hash rather than the routing key.
The state succeeds without changes when no matching binding exists.

To remove an exchange-to-exchange binding, include
`destination_type: exchange`:

```yaml
remove_exchange_binding:
  rabbitmq_management.binding_absent:
    - name: old-exchange-link
    - source: incoming
    - destination: retired-processing
    - destination_type: exchange
    - routing_key: orders.*
```

## Test mode

Salt test mode reports the predicted change without creating or deleting a
binding:

```bash
salt '*' state.apply rabbitmq_bindings test=True
```

When a change is required, the state returns `result: null` and describes the
predicted binding in `changes`. If the desired state is already satisfied, it
returns `result: true` with an empty `changes` mapping.

## State parameters

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Salt state identifier; it is not used to match a RabbitMQ binding. |
| `vhost` | no | `/` | RabbitMQ virtual host. |
| `source` | yes | — | Source exchange name. |
| `destination` | yes | — | Destination queue or exchange name. |
| `destination_type` | no | `queue` | Either `queue` or `exchange`. |
| `routing_key` | no | empty string | Routing key or topic pattern. |
| `arguments` | no | empty mapping | Binding arguments as a mapping or JSON object string. |

Additional keyword arguments are treated as Management API connection
overrides and are passed to every execution-module call made by the state.
