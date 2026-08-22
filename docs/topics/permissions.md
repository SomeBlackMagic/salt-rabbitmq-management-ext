# Managing RabbitMQ permissions

The `rabbitmq_management.permission_present` and
`rabbitmq_management.permission_absent` states manage RabbitMQ user permissions
through the Management API.

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
have administrator permissions to manage user permissions.

Connection settings can also be overridden in an individual state.

## What permissions are

RabbitMQ permissions control what a user can do within a virtual host. Each
permission is a regex triplet:

- **configure** — resources (queues, exchanges) the user may declare or delete
- **write** — resources the user may publish messages to
- **read** — resources the user may consume messages from

A user must have a permission record for a virtual host before they can
interact with any resource in it.

## Default full access

When all three regexes are `.*`, the user has unrestricted access to all
resources in the virtual host:

```yaml
app_user_permissions:
  rabbitmq_management.permission_present:
    - name: /production
    - user: app-service
    - configure: .*
    - write: .*
    - read: .*
```

When `configure`, `write`, and `read` are omitted, they default to `.*`.

## Restricting access

Grant a read-only service account access only to queues matching a specific
prefix:

```yaml
reporting_service_permissions:
  rabbitmq_management.permission_present:
    - name: /production
    - user: reporting
    - configure: ""
    - write: ""
    - read: "^reporting\\..*"
```

An empty string `""` means the user has no access at all for that category.

## Updating permissions

`permission_present` is idempotent. When the permission record already exists
with the desired values, no change is made. When any regex differs, the record
is updated. The `changes` return value shows only the fields that changed:

```python
{"old": {"write": ".*"}, "new": {"write": ""}}
```

## Removing permissions

Use `permission_absent` to revoke a user's access to a virtual host entirely:

```yaml
remove_legacy_permissions:
  rabbitmq_management.permission_absent:
    - name: /production
    - user: legacy-app
```

The state succeeds without changes when the permission record is already absent.

## Test mode

Salt test mode reports the predicted change without modifying any permission:

```bash
salt '*' state.apply rabbitmq_permissions test=True
```

When a change is required, the state returns `result: null` and describes the
predicted change in `changes`. If the desired state is already satisfied, it
returns `result: true` with an empty `changes` mapping.

## State parameters

### `permission_present`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Virtual host name. |
| `user` | yes | — | RabbitMQ user name. |
| `configure` | no | `.*` | Regex for resources the user may declare or delete. Use `""` to deny all. |
| `write` | no | `.*` | Regex for resources the user may publish to. Use `""` to deny all. |
| `read` | no | `.*` | Regex for resources the user may consume from. Use `""` to deny all. |

Additional keyword arguments are treated as Management API connection overrides
and are passed to every execution-module call made by the state.

### `permission_absent`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Virtual host name. |
| `user` | yes | — | RabbitMQ user name. |

Additional keyword arguments are treated as Management API connection overrides.
