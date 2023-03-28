# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import json
import logging
import re

import ops
import requests
from boto3 import client
from botocore.config import Config
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
    response = requests.get(
        f"http://{unit_informations[app.units[0].name]['address']}:8065", timeout=5
    )
    assert response.status_code == 200
    assert "Mattermost" in response.text


async def test_s3_storage(
    ops_test: OpsTest,
    model: ops.model.Model,
    app: Application,
    localstack_s3_config: dict,
):
    """
    arrange: after charm deployed and openstack swift server ready.
    act: update charm configuration for openstack object storage plugin.
    assert: a file should be uploaded to the openstack server and be accessible through it.
    """

    await app.set_config(
        {
            "s3_enabled": "true",
            "s3_endpoint": localstack_s3_config["url"],
            "s3_bucket": localstack_s3_config["bucket"],
            "s3_region": localstack_s3_config["region"],
            "s3_access_key_id": localstack_s3_config["credentials"]["access-key"],
            "s3_secret_access_key": localstack_s3_config["credentials"]["secret-key"],
            "s3_server_side_encryption": "false",
            "extra_env": '{"MM_FILESETTINGS_AMAZONS3SSL": "false","MM_SERVICESETTINGS_ENABLELOCALMODE": "true","MM_SERVICESETTINGS_LOCALMODESOCKETLOCATION": "/tmp/mattermost.socket"}',
        }
    )
    await model.wait_for_idle(status="active")

    # create a user
    cmd = "MMCTL_LOCAL_SOCKET_PATH=/tmp/mattermost.socket /mattermost/bin/mmctl --local user create --email test@test.test --username test --password thisisabadpassword"
    output = await ops_test.juju("run", "--application", app.name, cmd)

    # login to the API
    data = {"login_id": "test@test.test", "password": "thisisabadpassword"}
    cmd = f"curl -sid '{json.dumps(data)}' http://localhost:8065/api/v4/users/login"
    output = await ops_test.juju("run", "--application", app.name, cmd)
    token = ""
    for line in output[1].splitlines():
        if m := re.match(r"Token: (\w+)", line):
            token = m.group(1)

    # create a team
    data = {"name": "test", "display_name": "test", "type": "O"}
    cmd = f"curl -XPOST -sd '{json.dumps(data)}' -H 'authorization: Bearer {token}' http://localhost:8065/api/v4/teams"
    output = await ops_test.juju("run", "--application", app.name, cmd)
    team = json.loads(output[1])

    # create a channel
    data = {"team_id": team["id"], "name": "test", "display_name": "test", "type": "O"}
    cmd = f"curl -XPOST -sd '{json.dumps(data)}' -H 'authorization: Bearer {token}' http://localhost:8065/api/v4/channels"
    output = await ops_test.juju("run", "--application", app.name, cmd)
    channel = json.loads(output[1])

    # upload a file
    cmd = (
        "curl -F 'files=@/etc/os-release' -F 'channel_id="
        + channel["id"]
        + "' -H 'authorization: Bearer "
        + token
        + "' http://localhost:8065/api/v4/files"
    )
    output = await ops_test.juju("run", "--application", app.name, cmd)

    logger.info("Mattermost config updated, checking bucket content")

    # Configuration for boto client
    s3_client_config = Config(
        region_name=localstack_s3_config["region"],
        s3={
            "addressing_style": "virtual",
        },
    )

    # Trick to use when localstack is deployed on another location than locally
    if localstack_s3_config["ip_address"] != "127.0.0.1":
        proxy_definition = {
            "http": localstack_s3_config["url"],
        }
        s3_client_config = s3_client_config.merge(
            Config(
                proxies=proxy_definition,
            )
        )

    # Configure the boto client
    s3_client = client(
        "s3",
        localstack_s3_config["region"],
        aws_access_key_id=localstack_s3_config["credentials"]["access-key"],
        aws_secret_access_key=localstack_s3_config["credentials"]["secret-key"],
        endpoint_url=localstack_s3_config["endpoint"],
        use_ssl=False,
        config=s3_client_config,
    )

    # Check the bucket has been created
    response = s3_client.list_buckets()
    bucket_list = [*map(lambda a: a["Name"], response["Buckets"])]

    assert localstack_s3_config["bucket"] in bucket_list

    # Check content has been uploaded in the bucket
    response = s3_client.list_objects(Bucket=localstack_s3_config["bucket"])
    object_count = sum(1 for _ in response["Contents"])

    assert object_count > 0
