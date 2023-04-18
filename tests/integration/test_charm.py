# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import logging
import pathlib
import re
import time

import ops
import requests
from boto3 import client
from ops.model import Application
from pytest_operator.plugin import OpsTest

import utils

logger = logging.getLogger(__name__)


async def test_workload_online_default(
    ops_test: OpsTest,
    app: Application,
):
    """
    arrange: after charm deployed
    act: request the homepage of the application
    assert: the application should respond with 200 HTTP OK
    """
    response = requests.get(
        f"http://{await utils.get_mattermost_ip(ops_test, app)}:8065", timeout=5
    )
    assert response.status_code == 200
    assert "Mattermost" in response.text


async def test_s3_storage(
    ops_test: OpsTest,
    model: ops.model.Model,
    app: Application,
    localstack_s3_config: dict,
    tmp_path: pathlib.Path,
    localstack_s3_client: client,
    test_entities: dict,
):
    """
    arrange: after charm deployed and openstack swift server ready
    act: update charm configuration for openstack object storage plugin
    assert: a file should be uploaded to the openstack server and be accessible through it
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
        }
    )
    # An error state can sometimes be reached by Mattermost during s3 configuration
    await model.wait_for_idle(status="active", raise_on_error=False)

    mattermost_ip = await utils.get_mattermost_ip(ops_test, app)

    # create a test file
    test_file_name = "test_file.txt"
    test_file = tmp_path / test_file_name
    test_content = "This is a test file."
    test_file.write_text(test_content, encoding="utf-8")

    # upload the test file
    with open(test_file, "r", encoding="utf-8") as test_fd:
        response = requests.post(
            f"http://{mattermost_ip}:8065/api/v4/files",
            data={"channel_id": test_entities["channel"]["id"]},
            files={"file": test_fd},
            headers=test_entities["headers"],
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
    arrange: after charm is deployed and ready
    act: scale application to 3 units and kill the current leader
    assert: the application should be reachable
    """

    # get the pod name of the first unit (the leader)
    pods = kube_core_client.list_namespaced_pod(namespace=ops_test.model_name).items
    # the alphabet used by k8s is restricted to avoid bad words
    # https://github.com/kubernetes/kubernetes/blob/master/staging/src/k8s.io/apimachinery/pkg/util/rand/rand.go#L83
    k8s_pod_ending_regex = "[bcdfghjklmnpqrstvwxz2456789]{9,10}-[bcdfghjklmnpqrstvwxz2456789]{5}"
    mattermost_pod_regex = re.compile(f"mattermost-k8s-{k8s_pod_ending_regex}")
    leader_pod = next(
        p.metadata.name for p in pods if re.match(mattermost_pod_regex, p.metadata.name)
    )

    # scale the application
    await app.scale(scale=3)
    await ops_test.model.wait_for_idle(status="active")

    # kill the leader
    kube_core_client.delete_namespaced_pod(name=leader_pod, namespace=ops_test.model_name)
    await ops_test.model.wait_for_idle(status="active")

    response = requests.get(
        f"http://{await utils.get_mattermost_ip(ops_test, app)}:8065", timeout=5
    )
    assert response.status_code == 200
    assert "Mattermost" in response.text


async def test_reminder_plugin(
    ops_test: OpsTest,
    app: Application,
    test_entities,
):
    """
    arrange: after charm is deployed and ready
    act: enable the reminder plugin and execute a command to create a reminder
    assert: the plugin should be enabled and the reminder should be produced
    """

    plugin_name = "com.github.scottleedavis.mattermost-plugin-remind"
    cmd = (
        "MMCTL_LOCAL_SOCKET_PATH=/tmp/mattermost.socket /mattermost/bin/mmctl --local"
        f" plugin enable {plugin_name}"
    )
    await ops_test.juju("run", "--application", app.name, cmd)

    cmd = (
        "MMCTL_LOCAL_SOCKET_PATH=/tmp/mattermost.socket /mattermost/bin/mmctl --local"
        " plugin list"
    )
    output = await ops_test.juju("run", "--application", app.name, cmd)
    plugin_enabled = False
    for line in output[1].splitlines():
        if re.match(re.compile(plugin_name), line):
            plugin_enabled = True
            break
        if line == "Listing disabled plugins":
            break
    assert plugin_enabled, f"{plugin_name} is not in enabled plugins."

    mattermost_ip = await utils.get_mattermost_ip(ops_test, app)

    # execute a command
    reminder = "test01"
    data = {
        "channel_id": test_entities["channel"]["id"],
        "command": f"/remind ~{test_entities['channel']['name']} {reminder} in 1 minute",
    }
    requests.post(
        f"http://{mattermost_ip}:8065/api/v4/commands/execute",
        data=json.dumps(data),
        headers=test_entities["headers"],
        timeout=10,
    )

    # wait for the reminder to trigger
    time.sleep(120)

    # execute a command
    response = requests.get(
        f"http://{mattermost_ip}:8065/api/v4/channels/{test_entities['channel']['id']}/posts",
        headers=test_entities["headers"],
        timeout=10,
    )
    posts = response.json()
    assert any(
        (
            post[1]["message"] == f'@test asked me to remind you "{reminder}".'
            for post in posts["posts"].items()
        )
    ), "The reminder wasn't properly created."
