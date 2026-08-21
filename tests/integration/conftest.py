import os

import pytest
import requests


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):  # pragma: no cover
    """Point pytest-docker at the project-level compose.yaml."""
    return os.path.join(str(pytestconfig.rootdir), "compose.yaml")


@pytest.fixture(scope="session")
def rabbitmq_service(docker_ip, docker_services):  # pragma: no cover
    """
    Start a RabbitMQ container and wait until the Management API responds.

    Returns a dict of connection parameters that can be passed directly as
    keyword arguments to ``rabbitmq_management.*`` execution functions.
    """
    port = docker_services.port_for("rabbitmq", 15672)

    def is_ready():
        try:
            resp = requests.get(
                f"http://{docker_ip}:{port}/api/overview",
                auth=("guest", "guest"),
                timeout=3,
            )
            return resp.status_code == 200
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    docker_services.wait_until_responsive(timeout=60, pause=1, check=is_ready)

    return {
        "host": docker_ip,
        "port": port,
        "user": "guest",
        "password": "guest",
    }


@pytest.fixture(scope="package")
def master(master):  # pragma: no cover
    with master.started():
        yield master


@pytest.fixture(scope="package")
def minion(minion):  # pragma: no cover
    with minion.started():
        yield minion


@pytest.fixture
def salt_run_cli(master):  # pragma: no cover
    return master.salt_run_cli()


@pytest.fixture
def salt_cli(master):  # pragma: no cover
    return master.salt_cli()


@pytest.fixture
def salt_call_cli(minion):  # pragma: no cover
    return minion.salt_call_cli()


@pytest.fixture(scope="module")
def salt_ssh_cli(
    master, salt_ssh_roster_file, sshd_config_dir, known_hosts_file
):  # pylint: disable=unused-argument; pragma: no cover
    return master.salt_ssh_cli(
        timeout=180,
        roster_file=salt_ssh_roster_file,
        target_host="localhost",
        client_key=str(sshd_config_dir / "client_key"),
    )
