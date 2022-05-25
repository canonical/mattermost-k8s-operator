import pytest
from ops.model import ActiveStatus
from pytest_operator.plugin import OpsTest


@pytest.mark.abort_on_fail
async def juju_run(unit, cmd):
    """Helper function that runs a juju command"""
    result = await unit.run(cmd)
    code = result.results["Code"]
    stdout = result.results.get("Stdout")
    stderr = result.results.get("Stderr")
    assert code == "0", f"{cmd} failed ({code}): {stderr or stdout}"
    return stdout


async def test_build_and_deploy(ops_test: OpsTest):
    charm = await ops_test.build_charm(".")
    await ops_test.model.deploy("postgresql-k8s")
    await ops_test.model.deploy(charm)
    await ops_test.model.add_relation(
        "postgresql-k8s:db",
        "mattermost-k8s",
    )
    await ops_test.model.wait_for_idle(status=ActiveStatus.name)


async def test_status(ops_test: OpsTest):
    assert ops_test.model.applications["mattermost-k8s"].status == ActiveStatus.name
    assert ops_test.model.applications["postgresql-k8s"].status == ActiveStatus.name


async def test_workload_online_default(ops_test: OpsTest):
    app = ops_test.model.applications["postgresql-k8s"]
    unit = app.units[0]
    matt_unit = ops_test.model.applications["mattermost-k8s"]
    curl_output = await juju_run(unit, "curl {}".format(matt_unit.public_address + ":8065"))
    assert 'Mattermost' in curl_output
