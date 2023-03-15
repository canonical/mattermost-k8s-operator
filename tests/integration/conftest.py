# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Mattermost charm integration tests."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import docker
import pytest_asyncio
import yaml
from ops.model import ActiveStatus
from pytest import fixture
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@fixture(scope="module", name="metadata")
def metadata_fixture():
    """Provides charm metadata."""
    yield yaml.safe_load(Path("./metadata.yaml").read_text("utf-8"))


@fixture(scope="module", name="app_name")
def app_name_fixture(metadata):
    """Provides app name from the metadata."""
    yield metadata["name"]


@fixture(scope="module", name="mattermost_image")
def build_mattermost_image():
    image_name = f"localhost:32000/mattermost:{datetime.now().hour}-{datetime.now().minute}-{datetime.now().second}"
    client = docker.from_env()
    logger.info("Start building mattermost image")
    client.images.build(
        path="./",
        dockerfile="Dockerfile",
        tag=image_name,
        buildargs={"image_flavour": "canonical", "local_mode": "true"},
    )
    logger.info("Done.")
    logger.info("Start pushing mattermost image")
    client.images.push(image_name)
    logger.info("Done.")
    return image_name


@pytest_asyncio.fixture(scope="module")
async def app(
    ops_test: OpsTest,
    app_name: str,
    mattermost_image: str,
):
    """Mattermost charm used for integration testing.

    Builds the charm and deploys it and the relations it depends on.
    """
    assert ops_test.model
    await ops_test.model.deploy("postgresql-k8s"),

    charm = await ops_test.build_charm(".")
    application = await ops_test.model.deploy(charm, application_name=app_name, series="focal")
    await ops_test.model.wait_for_idle()

    # change the image that will be used for the mattermost container
    await application.set_config(
        {
            "mattermost_image_path": mattermost_image,
        }
    )
    await ops_test.model.wait_for_idle()

    await asyncio.gather(
        ops_test.model.add_relation(app_name, "postgresql-k8s:db"),
    )
    # mypy doesn't see that ActiveStatus has a name
    await ops_test.model.wait_for_idle(status=ActiveStatus.name, raise_on_error=False)  # type: ignore

    yield application


@fixture(scope="module")
def localstack_ip(request):
    """Get the localstack IP from the --localstack-ip argument.

    Return the IP address of a localstack instance
    """
    return request.config.getoption("--localstack-ip")


@fixture(scope="module")
def localstack_s3_config(localstack_ip: str) -> dict:
    """Generate a s3_config dict.

    Return a dict of s3 configurations
    """
    s3_config: dict = {
        # Localstack doesn't require any specific value there, any random string will work
        "credentials": {
            "access-key": "my-lovely-key",
            "secret-key": "this-is-very-secret",
        },
        # Localstack enforce to use this domain and it resolves to localhost
        "domain": "localhost.localstack.cloud",
        "bucket": "tests",
        "region": "us-east-1",
        "url": f"{localstack_ip}:4566",
    }

    # Parse URL to get the IP address and the port, and compose the required variables
    parsed_s3_url = urlparse(f"http://{localstack_ip}:4566")
    s3_ip_address = parsed_s3_url.hostname
    s3_endpoint = f"{parsed_s3_url.scheme}://{s3_config['domain']}"
    if parsed_s3_url:
        s3_endpoint = f"{s3_endpoint}:{parsed_s3_url.port}"
    s3_config["ip_address"] = s3_ip_address
    s3_config["endpoint"] = s3_endpoint
    return s3_config
