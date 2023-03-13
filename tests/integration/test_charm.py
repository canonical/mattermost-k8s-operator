# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

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
    assert ops_test.model
    charm = await ops_test.build_charm(".")
    await ops_test.model.deploy("postgresql-k8s")
    await ops_test.model.deploy(charm)
    await ops_test.model.wait_for_idle(raise_on_error=False)
    await ops_test.model.add_relation(
        "postgresql-k8s:db",
        "mattermost-k8s",
    )
    # mypy doesn't see that ActiveStatus has a name
    await ops_test.model.wait_for_idle(status=ActiveStatus.name, raise_on_error=False)  # type: ignore


async def test_status(ops_test: OpsTest):
    assert ops_test.model
    # mypy doesn't see that ActiveStatus has a name
    assert ops_test.model.applications["mattermost-k8s"].status == ActiveStatus.name  # type: ignore
    assert ops_test.model.applications["postgresql-k8s"].status == ActiveStatus.name  # type: ignore


async def test_workload_online_default(ops_test: OpsTest):
    assert ops_test.model
    app = ops_test.model.applications["mattermost-k8s"]
    mmost_unit = app.units[0]
    action = await mmost_unit.run("unit-get private-address")
    curl_output = await juju_run(
        mmost_unit, "curl {}:8065".format(action.results["Stdout"].replace("\n", ""))
    )
    assert "Mattermost" in curl_output
