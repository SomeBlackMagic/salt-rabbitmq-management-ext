# Managing RabbitMQ runtime parameters

The `rabbitmq_management.parameter_present` and
`rabbitmq_management.parameter_absent` states manage RabbitMQ runtime
parameters through the Management API.

A runtime parameter is a key-value store entry scoped to a component and
virtual host. Components include `federation-upstream`,
`federation-upstream-set`, `shovel`, and other plugins that use the parameter
system.

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
have permission to manage parameters in the selected virtual host.

Connection settings can also be overridden in an individual state.

## Creating and updating a parameter

Use `parameter_present` to ensure a parameter exists with a specific value:

```yaml
federation_upstream:
  rabbitmq_management.parameter_present:
    - name: remote-dc
    - component: federation-upstream
    - vhost: /
    - value:
        uri: amqp://remote-server.internal
        expires: 3600000
        prefetch-count: 1000
```

When the parameter already exists but its value differs from the desired
configuration, the parameter is updated. When the value matches, no change is
made.

## Shovel configuration

The same state works for shovel parameters:

```yaml
shovel_config:
  rabbitmq_management.parameter_present:
    - name: data-mover
    - component: shovel
    - vhost: /
    - value:
        src-uri: amqp://source.internal
        src-queue: source-queue
        dest-uri: amqp://destination.internal
        dest-queue: dest-queue
```

## JSON string value

The `value` parameter also accepts a JSON string. It is parsed before
comparison and before being sent to the API:

```yaml
federation_upstream_json:
  rabbitmq_management.parameter_present:
    - name: remote-dc
    - component: federation-upstream
    - vhost: /
    - value: '{"uri": "amqp://remote-server.internal", "expires": 3600000}'
```

## Removing a parameter

Use `parameter_absent` to ensure a parameter does not exist:

```yaml
remove_old_upstream:
  rabbitmq_management.parameter_absent:
    - name: old-upstream
    - component: federation-upstream
    - vhost: /
```

The state succeeds without changes when the parameter is already absent.

## Test mode

Salt test mode reports the predicted change without creating, updating, or
deleting a parameter:

```bash
salt '*' state.apply rabbitmq_parameters test=True
```

When a change is required, the state returns `result: null` and describes the
predicted change in `changes`. If the desired state is already satisfied, it
returns `result: true` with an empty `changes` mapping.

## State parameters — `parameter_present`

| Parameter | Required | Description |
| --- | --- | --- |
| `name` | yes | Parameter name. |
| `component` | yes | Component identifier (`federation-upstream`, `shovel`, etc.). |
| `vhost` | yes | RabbitMQ virtual host. |
| `value` | yes | Desired parameter value as a mapping or JSON string. |

Additional keyword arguments are treated as Management API connection
overrides and are passed to every execution-module call made by the state.

## State parameters — `parameter_absent`

| Parameter | Required | Description |
| --- | --- | --- |
| `name` | yes | Parameter name. |
| `component` | yes | Component identifier. |
| `vhost` | yes | RabbitMQ virtual host. |

Additional keyword arguments are treated as Management API connection overrides.
