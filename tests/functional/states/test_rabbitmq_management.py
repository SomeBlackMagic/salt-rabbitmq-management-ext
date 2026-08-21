import pytest

pytestmark = [
    pytest.mark.requires_salt_states(
        "rabbitmq_management.binding_present",
        "rabbitmq_management.binding_absent",
        "rabbitmq_management.vhost_present",
        "rabbitmq_management.vhost_absent",
    ),
]


@pytest.fixture
def rabbitmq_management(states):
    return states.rabbitmq_management


def test_vhost_states_are_available(rabbitmq_management):
    assert callable(rabbitmq_management.vhost_present)
    assert callable(rabbitmq_management.vhost_absent)


def test_binding_states_are_merged_into_shared_namespace(rabbitmq_management):
    assert callable(rabbitmq_management.binding_present)
    assert callable(rabbitmq_management.binding_absent)
