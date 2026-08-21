# Managing RabbitMQ policies

The `rabbitmq_management.policy_present` and `rabbitmq_management.policy_absent`
states manage RabbitMQ policies through the Management API.

A policy applies a set of optional arguments to queues, exchanges, or both
within a virtual host. All resources whose names match the policy pattern
inherit the policy definition. Policies with a higher priority value take
precedence when multiple policies match the same resource.

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
have administrator permissions to manage policies.

Connection settings can also be overridden in an individual state.

## Creating a policy

Use `policy_present` to ensure a policy exists with the desired configuration:

```yaml
ha_policy:
  rabbitmq_management.policy_present:
    - name: ha-all
    - vhost: /
    - pattern: ^.*
    - definition:
        ha-mode: all
        ha-sync-mode: automatic
```

When the policy already exists and its configuration matches, no change is
made. When any field differs, the policy is updated.

## Updating a policy

Updating a policy works the same way as creating one. Set the parameters to
their new values and apply the state:

```yaml
ha_policy_two_nodes:
  rabbitmq_management.policy_present:
    - name: ha-all
    - vhost: /
    - pattern: ^.*
    - definition:
        ha-mode: exactly
        ha-params: 2
        ha-sync-mode: automatic
    - priority: 10
```

The `changes` return value describes only the fields that changed:

```python
{"old": {"priority": 0}, "new": {"priority": 10}}
```

## Applying a policy to queues or exchanges only

Use `apply_to` to restrict which resource types the policy matches. Accepted
values are `all` (default), `queues`, and `exchanges`:

```yaml
queue_ttl_policy:
  rabbitmq_management.policy_present:
    - name: ttl-queues
    - vhost: /production
    - pattern: ^temp\.
    - definition:
        message-ttl: 60000
    - apply_to: queues

alternate_exchange_policy:
  rabbitmq_management.policy_present:
    - name: ae-exchanges
    - vhost: /production
    - pattern: ^.*
    - definition:
        alternate-exchange: backup-exchange
    - apply_to: exchanges
```

## Policy priority

When multiple policies match the same resource, RabbitMQ applies the policy
with the highest `priority` value. The default priority is `0`:

```yaml
critical_ha_policy:
  rabbitmq_management.policy_present:
    - name: ha-critical
    - vhost: /production
    - pattern: ^critical\.
    - definition:
        ha-mode: all
        ha-sync-mode: automatic
    - priority: 100
```

## JSON string definition

The `definition` parameter also accepts a JSON string. It is parsed before
comparison and before being sent to the API:

```yaml
ha_policy_json:
  rabbitmq_management.policy_present:
    - name: ha-all
    - vhost: /
    - pattern: ^.*
    - definition: '{"ha-mode": "all", "ha-sync-mode": "automatic"}'
```

## Common definition keys

**High availability:**

- `ha-mode`: `all`, `exactly`, `nodes`
- `ha-params`: number of replicas (for `exactly`) or list of node names (for `nodes`)
- `ha-sync-mode`: `automatic` or `manual`

**Queue limits:**

- `max-length`: maximum number of messages
- `max-length-bytes`: maximum total queue size in bytes
- `overflow`: `drop-head`, `reject-publish`, or `reject-publish-dlx`
- `message-ttl`: message TTL in milliseconds
- `expires`: queue expiration time in milliseconds

**Dead lettering:**

- `dead-letter-exchange`: exchange to route dead-lettered messages to
- `dead-letter-routing-key`: routing key for dead-lettered messages

**Federation:**

- `federation-upstream-set`: upstream set name

**Other:**

- `queue-mode`: `lazy` or `default`
- `delivery-limit`: maximum number of delivery attempts

## Removing a policy

Use `policy_absent` to ensure a policy does not exist:

```yaml
remove_old_policy:
  rabbitmq_management.policy_absent:
    - name: old-ha-policy
    - vhost: /
```

The state succeeds without changes when the policy is already absent.

## Test mode

Salt test mode reports the predicted change without modifying any policy:

```bash
salt '*' state.apply rabbitmq_policies test=True
```

When a change is required, the state returns `result: null` and describes the
predicted change in `changes`. If the desired state is already satisfied, it
returns `result: true` with an empty `changes` mapping.

## State parameters

### `policy_present`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Policy name. |
| `vhost` | yes | — | RabbitMQ virtual host. |
| `pattern` | yes | — | Regex pattern to match queue or exchange names. |
| `definition` | yes | — | Policy definition as a mapping or JSON string. |
| `priority` | no | `0` | Policy priority. Higher value takes precedence. |
| `apply_to` | no | `all` | Resource types to apply the policy to: `all`, `queues`, or `exchanges`. |

Additional keyword arguments are treated as Management API connection
overrides and are passed to every execution-module call made by the state.

### `policy_absent`

| Parameter | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | — | Policy name to remove. |
| `vhost` | yes | — | RabbitMQ virtual host. |

Additional keyword arguments are treated as Management API connection overrides.
