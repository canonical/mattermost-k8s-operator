# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import logging
import re
import pathlib
from typing import Dict

import ops
import requests
from boto3 import client
from ops.model import Application
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


async def test_workload_online_default(
    ops_test: OpsTest,
    app: Application,
):
    unit_informations = json.loads(
        (await ops_test.juju("show-unit", app.units[0].name, "--format", "json"))[1]
    )
    mattermost_ip = unit_informations[app.units[0].name]["address"]
    response = requests.get(f"http://{mattermost_ip}:8065", timeout=5)
    assert response.status_code == 200
    assert "Mattermost" in response.text


async def test_s3_storage(
    ops_test: OpsTest,
    model: ops.model.Model,
    app: Application,
    localstack_s3_config: dict,
    test_user: Dict[str, str],
    tmp_path: pathlib.Path,
    localstack_s3_client: client,
):
    """
    arrange: after charm deployed and openstack swift server ready.
    act: update charm configuration for openstack object storage plugin.
    assert: a file should be uploaded to the openstack server and be accessible through it.
    """

    await app.set_config(
        {
            "s3_enabled": "true",
            "s3_endpoint": localstack_s3_config["endpoint_without_scheme"],
            "s3_bucket": localstack_s3_config["bucket"],
            "s3_region": localstack_s3_config["region"],
            "s3_access_key_id": localstack_s3_config["credentials"]["access-key"],
            "s3_secret_access_key": localstack_s3_config["credentials"]["secret-key"],
            "s3_server_side_encryption": "false",
            "extra_env": json.dumps(
                {
                    "MM_FILESETTINGS_AMAZONS3SSL": "false",
                    "MM_SERVICESETTINGS_ENABLELOCALMODE": "true",
                    "MM_SERVICESETTINGS_LOCALMODESOCKETLOCATION": "/tmp/mattermost.socket",
                }
            ),
        }
    )
    # An error state can sometimes be reached by Mattermost during s3 configuration
    await model.wait_for_idle(status="active", raise_on_error=False)

    unit_informations = json.loads(
        (await ops_test.juju("show-unit", app.units[0].name, "--format", "json"))[1]
    )
    mattermost_ip = unit_informations[app.units[0].name]["address"]

    # create a user
    cmd = (
        f"MMCTL_LOCAL_SOCKET_PATH=/tmp/mattermost.socket /mattermost/bin/mmctl"
        f" --local user create --email {test_user['login_id']} --username test"
        f" --password {test_user['password']}"
    )
    await ops_test.juju("run", "--application", app.name, cmd)

    # login to the API
    response = requests.post(
        f"http://{mattermost_ip}:8065/api/v4/users/login", data=json.dumps(test_user), timeout=10
    )
    headers = {"authorization": f"Bearer {response.headers['Token']}"}

    # create a team
    data = {"name": "test", "display_name": "test", "type": "O"}
    response = requests.post(
        f"http://{mattermost_ip}:8065/api/v4/teams",
        data=json.dumps(data),
        headers=headers,
        timeout=10,
    )
    team = response.json()

    # create a channel
    data = {"team_id": team["id"], "name": "test", "display_name": "test", "type": "O"}
    response = requests.post(
        f"http://{mattermost_ip}:8065/api/v4/channels",
        data=json.dumps(data),
        headers=headers,
        timeout=10,
    )
    channel = response.json()

    # create a test file
    test_file_name = "test_file.txt"
    test_file = tmp_path / test_file_name
    test_content = "This is a test file."
    test_file.write_text(test_content, encoding="utf-8")

    # upload the test file
    await ops_test.juju("run", "--application", app.name, cmd)
    with open(test_file, "r", encoding="utf-8") as test_fd:
        response = requests.post(
            f"http://{mattermost_ip}:8065/api/v4/files",
            data={"channel_id": channel["id"]},
            files={"file": test_fd},
            headers=headers,
            timeout=10,
        )

    logger.info("Mattermost config updated, checking bucket content")

    # Check the bucket has been created
    response = localstack_s3_client.list_buckets()
    bucket_list = [*map(lambda a: a["Name"], response["Buckets"])]

    assert localstack_s3_config["bucket"] in bucket_list

    # Check content has been uploaded in the bucket
    response = localstack_s3_client.list_objects(Bucket=localstack_s3_config["bucket"])
    object_count = sum(1 for _ in response["Contents"])
    assert object_count > 0
    test_file_key = next(x["Key"] for x in response["Contents"] if test_file_name in x["Key"])
    downloaded_test_file = tmp_path / "downloaded_test_file.txt"
    localstack_s3_client.download_file(
        localstack_s3_config["bucket"], test_file_key, downloaded_test_file
    )
    with open(downloaded_test_file, "r", encoding="utf-8") as test_fd:
        assert test_content in test_fd.read()


async def test_scale_workload(
    ops_test: OpsTest,
    app: Application,
    kube_core_client,
):
    """
    arrange: after charm deployed and ready.
    act: scale application to 3 units and kill the current leader.
    assert: the application should be reachable.
    """

    # get the pod name of the first unit (the leader)
    model_name = list(ops_test.models.values())[0].model_name
    leader_pod = next(
        p.metadata.name
        for p in kube_core_client.list_namespaced_pod(namespace=model_name).items
        if re.match(r"mattermost-k8s-\w{10}-\w{5}", p.metadata.name)
    )

    # scale the application
    await ops_test.juju("scale-application", "mattermost-k8s", "3")
    await ops_test.model.wait_for_idle(status="active")

    # kill the leader
    kube_core_client.delete_namespaced_pod(name=leader_pod, namespace=model_name)
    await ops_test.model.wait_for_idle(status="active")

    unit_informations = json.loads(
        (await ops_test.juju("show-unit", app.units[0].name, "--format", "json"))[1]
    )
    mattermost_ip = unit_informations[app.units[0].name]["address"]
    response = requests.get(f"http://{mattermost_ip}:8065", timeout=5)
    assert response.status_code == 200
    assert "Mattermost" in response.text
