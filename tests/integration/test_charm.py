import pytest
from ops.model import Application
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


async def test_workload_online_default(ops_test: OpsTest, app: Application):
    assert ops_test.model
    mmost_unit = app.units[0]
    action = await mmost_unit.run("unit-get private-address")
    curl_output = await juju_run(
        mmost_unit, "curl {}:8065".format(action.results["Stdout"].replace("\n", ""))
    )
    assert "Mattermost" in curl_output
