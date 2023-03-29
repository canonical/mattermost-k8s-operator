# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Mattermost charm integration tests."""

import asyncio
import json
import logging
import secrets
from pathlib import Path
from urllib.parse import urlparse

from ops.model import ActiveStatus, Application
from pytest import fixture
from pytest import FixtureRequest
import kubernetes
import ops
import pytest_asyncio
import yaml
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


@fixture(scope="module")
def mattermost_image(request):
    """Get the mattermost image name from the --mattermost-image argument.

    Return a the mattermost image name
    """
    return request.config.getoption("--mattermost-image")


@fixture(scope="module")
def test_user():
    """Create login informations for a test user.

    Return a dict with the users informations
    """
    return {"login_id": "test@test.test", "password": secrets.token_hex()}


@pytest_asyncio.fixture(scope="module", name="model")
async def model_fixture(ops_test: OpsTest) -> ops.model.Model:
    """The current test model."""
    assert ops_test.model
    return ops_test.model


@pytest_asyncio.fixture(scope="module")
async def app(
    ops_test: OpsTest,
    model: ops.model.Model,
    app_name: str,
    mattermost_image: str,
):
    """Mattermost charm used for integration testing.

    Builds the charm and deploys it and the relations it depends on.
    """
    await model.deploy("postgresql-k8s"),

    charm = await ops_test.build_charm(".")
    application = await model.deploy(charm, application_name=app_name, series="focal")
    await model.wait_for_idle()

    # change the image that will be used for the mattermost container
    await application.set_config(
        {
            "mattermost_image_path": mattermost_image,
        }
    )
    await model.wait_for_idle()

    await asyncio.gather(
        model.add_relation(app_name, "postgresql-k8s:db"),
    )
    # mypy doesn't see that ActiveStatus has a name
    await model.wait_for_idle(status=ActiveStatus.name)  # type: ignore

    yield application


@pytest_asyncio.fixture(scope="module")
async def mattermost_ip(
    ops_test: OpsTest,
    app: Application,
):
    """Get the IP address of the first unit of mattermost.

    Return the IP address of a mattermost unit.
    """
    unit_informations = json.loads(
        (await ops_test.juju("show-unit", app.units[0].name, "--format", "json"))[1]
    )
    return unit_informations[app.units[0].name]["address"]


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
            "access-key": "test-access-key",
            "secret-key": secrets.token_hex(),
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


@fixture(scope="module", name="kube_config")
def kube_config_fixture(request: FixtureRequest):
    """The Kubernetes cluster configuration file."""
    kube_config = request.config.getoption("--kube-config")
    assert kube_config, (
        "The Kubernetes config file path should not be empty, "
        "please include it in the --kube-config parameter"
    )
    return kube_config


@fixture(scope="module", name="kube_core_client")
def kube_core_client_fixture(kube_config):
    """Create a kubernetes client for core API v1."""
    kubernetes.config.load_kube_config(config_file=kube_config)
    kubernetes_client_v1 = kubernetes.client.CoreV1Api()
    return kubernetes_client_v1
