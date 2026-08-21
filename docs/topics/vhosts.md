# Managing RabbitMQ virtual hosts

The `rabbitmq_management.vhost_present` and `rabbitmq_management.vhost_absent`
states manage RabbitMQ virtual hosts through the RabbitMQ Management API.

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
have administrator permissions to manage virtual hosts.

Connection settings can also be overridden in an individual state. For
example, `timeout: 10` is passed to every Management API call made by that
state.

## Creating a virtual host

Use `vhost_present` to ensure a virtual host exists:

```yaml
production_vhost:
  rabbitmq_management.vhost_present:
    - name: /production
```

Applying the state again does not modify the virtual host when it already
exists with no managed fields specified.

## Configuring a virtual host

`vhost_present` manages the following optional fields:

```yaml
production_vhost:
  rabbitmq_management.vhost_present:
    - name: /production
    - description: Production environment vhost
    - tags:
      - production
      - critical
    - default_queue_type: quorum
    - tracing: false
```

Fields set to `None` (or omitted) are left unmanaged — the state does not
change their current value. Empty strings and empty lists are explicit values
and can be used to clear a field:

```yaml
clear_vhost_metadata:
  rabbitmq_management.vhost_present:
    - name: /production
    - description: ""
    - tags: []
```

### Tags

Tags can be supplied as a list or as a comma-separated string:

```yaml
  - tags: production, critical
```

Tag order is ignored when comparing the current state with the desired state.

### Default queue type

`default_queue_type` sets the queue type used when a queue is created without
an explicit type. Accepted values are `classic`, `quorum`, and `stream`.

```yaml
quorum_vhost:
  rabbitmq_management.vhost_present:
    - name: /services
    - default_queue_type: quorum
```

### Tracing

`tracing` enables or disables message tracing for the virtual host. Omit the
field or set it to `null` to leave the current tracing setting unchanged.

```yaml
  - tracing: false
```

## Removing a virtual host

Use `vhost_absent` to ensure a virtual host does not exist:

```yaml
old_vhost:
  rabbitmq_management.vhost_absent:
    - name: /old-environment
```

The state succeeds without changes when the virtual host is already absent.

## Test mode

Salt test mode reports the predicted change without modifying any virtual host:

```bash
salt '*' state.apply rabbitmq_vhosts test=True
```

When a change is required, the state returns `result: null` and describes the
predicted change in `changes`. If the desired state is already satisfied, it
returns `result: true` with an empty `changes` mapping.

## Managing virtual host limits

Use `vhost_limit_present` to enforce a limit on a virtual host and
`vhost_limit_absent` to remove one.

Supported limit types:

- `max-connections` — maximum number of concurrent connections
- `max-queues` — maximum number of queues

### Setting a limit

```yaml
production_vhost_connections:
  rabbitmq_management.vhost_limit_present:
    - name: /production
    - limit_type: max-connections
    - value: 1000

production_vhost_queues:
  rabbitmq_management.vhost_limit_present:
    - name: /production
    - limit_type: max-queues
    - value: 500
```

The state is idempotent: if the limit is already set to the requested value,
no change is made. If the limit exists with a different value, it is updated.

Use `-1` to allow unlimited connections or queues while still managing the
limit through Salt:

```yaml
unlimited_connections:
  rabbitmq_management.vhost_limit_present:
    - name: /development
    - limit_type: max-connections
    - value: -1
```

### Removing a limit

```yaml
remove_connection_limit:
  rabbitmq_management.vhost_limit_absent:
    - name: /staging
    - limit_type: max-connections
```

The state succeeds without changes when the limit is already absent.

## State parameters

### `vhost_present`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Virtual host name. |
| `description` | no | unmanaged | Human-readable description. Empty string clears the field. |
| `tags` | no | unmanaged | List or comma-separated string of tags. Empty list clears the field. |
| `default_queue_type` | no | unmanaged | Default queue type: `classic`, `quorum`, or `stream`. |
| `tracing` | no | unmanaged | Enable (`true`) or disable (`false`) message tracing. |

### `vhost_absent`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Virtual host name to remove. |

### `vhost_limit_present`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Virtual host name. |
| `limit_type` | yes | — | Limit type: `max-connections` or `max-queues`. |
| `value` | yes | — | Limit value. Use `-1` for unlimited. |

### `vhost_limit_absent`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Virtual host name. |
| `limit_type` | yes | — | Limit type to remove: `max-connections` or `max-queues`. |

Additional keyword arguments are treated as Management API connection
overrides and are passed to every execution-module call made by the state.
