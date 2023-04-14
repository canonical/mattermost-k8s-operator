# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Some utility functions used in integration tests."""

import json

import requests
from ops.model import Application
from pytest_operator.plugin import OpsTest


async def get_mattermost_ip(
    ops_test: OpsTest,
    app: Application,
):
    """Get the IP address of the leader unit of mattermost.

    Args:
        ops_test: The pytest_operator model
        app: The mattermost application

    Returns:
        the IP address of the leader mattermost unit.
    """
    for unit in app.units:
        unit_informations = json.loads(
            (await ops_test.juju("show-unit", unit.name, "--format", "json"))[1]
        )
        if unit_informations[unit.name]["leader"]:
            return unit_informations[unit.name]["address"]


async def is_mattermost_reachable(mattermost_ip: str) -> bool:
    """Test if the mattermost application is reachable.

    Args:
        mattermost_ip: the IP of the mattermost application

    Returns:
        True if mattermost is reachable, False otherwise.
    """
    try:
        response = requests.get(f"http://{mattermost_ip}:8065", timeout=5)
        if response.status_code == 200:
            return True
    except requests.ConnectionError:
        return False
    except requests.Timeout:
        return False
    return False
