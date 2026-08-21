# Managing RabbitMQ users

The `rabbitmq_management.user_present` and `rabbitmq_management.user_absent`
states manage RabbitMQ users through the RabbitMQ Management API.

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
have administrator permissions to manage users.

## Creating a user

Use `user_present` to ensure a user exists:

```yaml
myapp_user:
  rabbitmq_management.user_present:
    - name: myapp
    - password: sdb://vault/rabbitmq/myapp/password
    - tags:
      - monitoring
      - management
```

## Managing user limits

Use `user_limit_present` to enforce a per-user limit and `user_limit_absent`
to remove one.

Supported limit types:

- `max-connections` — maximum number of concurrent connections for the user
- `max-channels` — maximum number of channels across all connections

### Setting a limit

```yaml
app_user_channels:
  rabbitmq_management.user_limit_present:
    - name: myapp
    - limit_type: max-channels
    - value: 100

app_user_connections:
  rabbitmq_management.user_limit_present:
    - name: myapp
    - limit_type: max-connections
    - value: 50
```

The state is idempotent: if the limit is already set to the requested value,
no change is made. If the limit exists with a different value, it is updated.

Use `-1` to allow unlimited connections or channels while still managing the
limit through Salt:

```yaml
unlimited_channels:
  rabbitmq_management.user_limit_present:
    - name: myapp
    - limit_type: max-channels
    - value: -1
```

### Removing a limit

```yaml
remove_user_limit:
  rabbitmq_management.user_limit_absent:
    - name: myapp
    - limit_type: max-channels
```

The state succeeds without changes when the limit is already absent.

## Removing a user

Use `user_absent` to ensure a user does not exist:

```yaml
remove_old_user:
  rabbitmq_management.user_absent:
    - name: olduser
```

## Test mode

Salt test mode reports the predicted change without modifying any user or
limit:

```bash
salt '*' state.apply rabbitmq_users test=True
```

## State parameters

### `user_present`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | RabbitMQ user name. |
| `password` | no | unmanaged | Password to set. Values starting with `sdb://` are resolved through Salt SDB. `None` leaves the password unmanaged. |
| `tags` | no | unmanaged | List or comma-separated string of tags. |
| `hashing_algorithm` | no | unmanaged | RabbitMQ password hashing algorithm. |

### `user_absent`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | RabbitMQ user name to remove. |

### `user_limit_present`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | RabbitMQ user name. |
| `limit_type` | yes | — | Limit type: `max-connections` or `max-channels`. |
| `value` | yes | — | Limit value. Use `-1` for unlimited. |

### `user_limit_absent`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | RabbitMQ user name. |
| `limit_type` | yes | — | Limit type to remove: `max-connections` or `max-channels`. |

Additional keyword arguments are treated as Management API connection
overrides and are passed to every execution-module call made by the state.
