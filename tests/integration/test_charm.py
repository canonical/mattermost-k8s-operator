import pytest
from ops.model import ActiveStatus, WaitingStatus 
from pytest_operator.plugin import OpsTest

@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest):

    charm = await ops_test.build_charm(".")
    await ops_test.model.deploy("postgresql-k8s")
    await ops_test.model.deploy(charm)
    await ops_test.model.add_relation(
        "postgresql-k8s:db",
        "mattermost-k8s",
    )
    await ops_test.model.wait_for_idle(wait_for_active=True)


async def test_status(ops_test: OpsTest):
    assert ops_test.model.applications["mattermost-k8s"].status == ActiveStatus.name
    assert ops_test.model.applications["postgresql-k8s"].status == ActiveStatus.name