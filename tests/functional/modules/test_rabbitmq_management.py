import pytest

pytestmark = [
    pytest.mark.requires_salt_modules(
        "rabbitmq_management.test_management_api",
        "rabbitmq_management.vhost_list",
        "rabbitmq_management.user_list",
        "rabbitmq_management.queue_list",
        "rabbitmq_management.policy_list",
    ),
]


@pytest.fixture
def rabbitmq_management(modules):
    return modules.rabbitmq_management


def test_domain_modules_are_merged_into_one_namespace(rabbitmq_management):
    assert callable(rabbitmq_management.test_management_api)
    assert callable(rabbitmq_management.vhost_list)
    assert callable(rabbitmq_management.user_list)
    assert callable(rabbitmq_management.queue_list)
    assert callable(rabbitmq_management.policy_list)
