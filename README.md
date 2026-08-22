# Salt Extension for RabbitMQ Management

A Salt extension for managing RabbitMQ through the [Management HTTP API][rabbitmq-management-api].
No CLI tools are required on the target host — all operations go over HTTP.

It provides both execution modules (for ad-hoc queries and automation) and state modules
(for idempotent, declarative configuration of RabbitMQ resources).

## What it manages

| Resource | State functions |
|----------|----------------|
| Virtual hosts | `vhost_present`, `vhost_absent` |
| Users | `user_present`, `user_absent` |
| Permissions | `permission_present`, `permission_absent` |
| Queues | `queue_present`, `queue_absent` |
| Exchanges | `exchange_present`, `exchange_absent` |
| Bindings | `binding_present`, `binding_absent` |
| Policies | `policy_present`, `policy_absent` |
| Parameters | `parameter_present`, `parameter_absent` |
| Federation upstreams | `federation_upstream_present`, `federation_upstream_absent` |
| Shovels | `shovel_present`, `shovel_absent` |
| User limits | `user_limit_present`, `user_limit_absent` |
| Virtual host limits | `vhost_limit_present`, `vhost_limit_absent` |

## Installation

```bash
pip install saltext-rabbitmq-management
```

Or via Salt's extension system:

```bash
salt-pip install saltext-rabbitmq-management
```

## Quick start

**Pillar / minion config:**

```yaml
rabbitmq:
  management:
    config:
      host: rabbitmq.example.com
      port: 15672
      user: salt
      password: secret
```

**Ensure a vhost and user exist:**

```yaml
production_vhost:
  rabbitmq_management.vhost_present:
    - name: /production

myapp_user:
  rabbitmq_management.user_present:
    - name: myapp
    - password: sdb://vault/rabbitmq/myapp
    - tags:
      - monitoring
```

**Ensure a queue exists:**

```yaml
orders_queue:
  rabbitmq_management.queue_present:
    - name: orders
    - vhost: /production
    - durable: true
    - arguments:
        x-queue-type: quorum
```

## Documentation

Full reference: [User Documentation][docs]

Available guides:

* [Managing RabbitMQ bindings](docs/topics/bindings.md)
* [Managing RabbitMQ exchanges](docs/topics/exchanges.md)
* [Managing RabbitMQ federation](docs/topics/federation.md)
* [Managing RabbitMQ permissions](docs/topics/permissions.md)
* [Managing RabbitMQ policies](docs/topics/policies.md)
* [Managing RabbitMQ parameters](docs/topics/parameters.md)
* [Managing RabbitMQ queues](docs/topics/queues.md)
* [Managing RabbitMQ shovels](docs/topics/shovels.md)
* [Managing RabbitMQ users](docs/topics/users.md)
* [Managing RabbitMQ virtual hosts](docs/topics/vhosts.md)

## Security

If you discover a security vulnerability, please refer
to [Salt's security guide][security].

## Contributing

The saltext-rabbitmq-management project welcomes contributions from anyone!

The [Salt Extensions guide][salt-extensions-guide] provides comprehensive instructions on all aspects
of Salt extension development, including [writing tests][writing-tests], [running tests][running-tests],
[writing documentation][writing-docs] and [rendering the docs][rendering-docs].

### Quickstart

To get started contributing, first clone this repository (or your fork):

```bash
# Clone the repo
git clone --origin upstream git@github.com:SomeBlackMagic/salt-rabbitmq-management-ext.git

# Change to the repo dir
cd saltext-rabbitmq-management
```

#### Automatic
If you have installed [direnv][direnv], copying the included `.envrc.example` to `.envrc` and
allowing it to run ensures a proper development environment is present and the virtual environment is active.

Without `direnv`, you can still run the automation explicitly:

```bash
make dev  # or python3 tools/initialize.py
source .venv/bin/activate
```

#### Manual
Please follow the [first steps][first-steps], skipping the repository initialization and first commit.

### Pull request

Always make changes in a feature branch:

```bash
git switch -c my-feature-branch
```

Please ensure you include a [news fragment](https://salt-extensions.github.io/salt-extension-copier/topics/documenting/changelog.html#procedure)
describing your changes. This is a requirement for all user-facing changes (bug fixes, new features),
with the exception of documentation changes.

To [submit a Pull Request][submitting-pr], you'll need a fork of this repository in
your own GitHub account. If you followed the instructions above,
set your fork as the `origin` remote now:

```bash
git remote add origin git@github.com:<your_fork>.git
```

Ensure you followed the [first steps][first-steps] and commit your changes, fixing any
failing `pre-commit` hooks. Then push the feature branch to your fork and submit a PR.

### Ways to contribute

Contributions come in many forms, and they're all valuable! Here are some ways you can help
without writing code:

* **Documentation**: Especially examples showing how to use this project
  to solve specific problems.
* **Triaging issues**: Help manage [issues][issues] and participate in [discussions][discussions].
* **Reviewing [Pull Requests][PRs]**: We especially appreciate reviews using [Conventional Comments][comments].

You can also contribute by:

* Writing blog posts
* Sharing your experiences using Salt + RabbitMQ Management
  on social media
* Giving talks at conferences
* Publishing videos
* Engaging in IRC, Discord or email groups

Any of these things are super valuable to our community, and we sincerely
appreciate every contribution!

[rabbitmq-management-api]: https://www.rabbitmq.com/docs/management#http-api
[security]: https://github.com/saltstack/salt/blob/master/SECURITY.md
[salt-extensions-guide]: https://salt-extensions.github.io/salt-extension-copier/
[writing-tests]: https://salt-extensions.github.io/salt-extension-copier/topics/testing/writing.html
[running-tests]: https://salt-extensions.github.io/salt-extension-copier/topics/testing/running.html
[writing-docs]: https://salt-extensions.github.io/salt-extension-copier/topics/documenting/writing.html
[rendering-docs]: https://salt-extensions.github.io/salt-extension-copier/topics/documenting/building.html
[first-steps]: https://salt-extensions.github.io/salt-extension-copier/topics/creation.html#initialize-the-python-virtual-environment
[submitting-pr]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork
[direnv]: https://direnv.net
[issues]: https://github.com/SomeBlackMagic/salt-rabbitmq-management-ext/issues
[PRs]: https://github.com/SomeBlackMagic/salt-rabbitmq-management-ext/pulls
[discussions]: https://github.com/SomeBlackMagic/salt-rabbitmq-management-ext/discussions
[comments]: https://conventionalcomments.org/
[docs]: https://SomeBlackMagic.github.io/salt-rabbitmq-management-ext/
