# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Mattermost charm integration tests."""

import asyncio
import json
import logging
import secrets
from pathlib import Path
from urllib.parse import urlparse

import kubernetes
import ops
import pytest_asyncio
import requests
import yaml
from boto3 import client
from botocore.config import Config
from ops.model import ActiveStatus, Application
from pytest import FixtureRequest, fixture
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


async def get_mattermost_ip(
    ops_test: OpsTest,
    app: Application,
):
    """Get the IP address of the leader unit of mattermost.

    Return the IP address of the leader mattermost unit.
    """
    for unit in app.units:
        unit_informations = json.loads(
            (await ops_test.juju("show-unit", unit.name, "--format", "json"))[1]
        )
        if unit_informations[unit.name]["leader"]:
            return unit_informations[unit.name]["address"]


@fixture(scope="module", name="metadata")
def metadata_fixture():
    """Provide charm metadata."""
    yield yaml.safe_load(Path("./metadata.yaml").read_text("utf-8"))


@fixture(scope="module", name="app_name")
def app_name_fixture(metadata):
    """Provide app name from the metadata."""
    yield metadata["name"]


@fixture(scope="module")
def mattermost_image(request):
    """Get the mattermost image name from the --mattermost-image argument.

    Return a the mattermost image name
    """
    return request.config.getoption("--mattermost-image")


@pytest_asyncio.fixture(scope="module", name="model")
async def model_fixture(ops_test: OpsTest) -> ops.model.Model:
    """Provide current test model."""
    assert ops_test.model
    MODEL_CONFIG = {"logging-config": "<root>=INFO;unit=DEBUG"}
    await ops_test.model.set_config(MODEL_CONFIG)
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

    # Change the image that will be used for the mattermost container
    # and use some common test configuration extra env variables
    await application.set_config(
        {
            "mattermost_image_path": mattermost_image,
            "extra_env": json.dumps(
                {
                    "MM_FILESETTINGS_AMAZONS3SSL": "false",
                    "MM_SERVICESETTINGS_ENABLELOCALMODE": "true",
                    "MM_SERVICESETTINGS_LOCALMODESOCKETLOCATION": "/tmp/mattermost.socket",
                }
            ),
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
async def test_entities(
    ops_test: OpsTest,
    app: Application,
):
    mattermost_ip = await get_mattermost_ip(ops_test, app)

    test_user = {"login_id": "test@test.test", "password": secrets.token_hex()}

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
    token = response.headers["Token"]
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

    yield {
        "token": token,
        "headers": headers,
        "user": {
            "email": test_user["login_id"],
            "password": test_user["password"],
        },
        "team": team,
        "channel": channel,
    }


@fixture(scope="module")
def localstack_url(request):
    """Get the localstack URL from the --localstack-url argument.

    Return the URL of a localstack instance
    """
    return request.config.getoption("--localstack-url")


@fixture(scope="module")
def localstack_s3_config(localstack_url: str) -> dict:
    """Generate a s3_config dict.

    Return a dict of s3 configurations
    """
    # Localstack enforce to use this domain and it resolves to localhost
    localstack_domain = "localhost.localstack.cloud"

    # Parse URL to get the IP address and the port, and compose the required variables
    parsed_s3_url = urlparse(localstack_url)

    s3_config: dict = {
        # Localstack doesn't require any specific value there, any random string will work
        "credentials": {
            "access-key": "test-access-key",
            "secret-key": secrets.token_hex(),
        },
        "domain": localstack_domain,
        "bucket": "tests",
        "region": "us-east-1",
        "url": localstack_url,
        "ip_address": parsed_s3_url.hostname,
        "endpoint": f"{parsed_s3_url.scheme}://{parsed_s3_url.hostname}:{parsed_s3_url.port}",
        # mattermost doesn't want the scheme
        "endpoint_without_scheme": f"{parsed_s3_url.hostname}:{parsed_s3_url.port}",
    }
    return s3_config


@fixture(scope="module")
def localstack_s3_client(localstack_s3_config: dict) -> client:
    """Generate a s3_client.

    Return a s3_client based on the localstack s3 config
    """
    # Configuration for boto client
    s3_client_config = Config(
        region_name=localstack_s3_config["region"],
        s3={
            "addressing_style": "virtual",
        },
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

    return s3_client


@fixture(scope="module", name="kube_config")
def kube_config_fixture(request: FixtureRequest):
    """Return the Kubernetes cluster configuration file."""
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
