# Copyright 2020 Canonical Ltd.
# Licensed under the GPLv3, see LICENCE file for details.

import logging

import pytest
from boto3 import client
from botocore.config import Config
from ops.model import Application
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


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


async def test_s3_storage(
    ops_test: OpsTest,
    app: Application,
    localstack_s3_config: dict,
):
    """
    arrange: after charm deployed and openstack swift server ready.
    act: update charm configuration for openstack object storage plugin.
    assert: a file should be uploaded to the openstack server and be accessible through it.
    """

    assert ops_test.model

    await app.set_config(
        {
            "s3_enabled": "true",
            "s3_endpoint": localstack_s3_config["url"],
            "s3_bucket": localstack_s3_config["bucket"],
            "s3_region": localstack_s3_config["region"],
            "s3_access_key_id": localstack_s3_config["credentials"]["access-key"],
            "s3_secret_access_key": localstack_s3_config["credentials"]["secret-key"],
            "s3_server_side_encryption": "false",
            "s3_tls": "false",
        }
    )

    await ops_test.model.wait_for_idle(status="active")

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
