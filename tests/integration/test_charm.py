#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Mattermost charm."""

import json
import logging

import jubilant
import pytest
import requests
from boto3 import client as s3_client_factory
from botocore.config import Config

from .conftest import generate_s3_config

logger = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
def test_active(app: str, juju: jubilant.Juju):
    """Check that the charm is active after deployment.

    arrange: The charm has been built and deployed with postgresql.
    act: Get the Juju status.
    assert: The mattermost-k8s and postgresql-k8s units are active.
    """
    status = juju.status()
    assert status.apps[app].units[app + "/0"].is_active
    assert status.apps["postgresql-k8s"].units["postgresql-k8s/0"].is_active


@pytest.mark.abort_on_fail
def test_workload_online(mattermost_address: str, juju: jubilant.Juju):
    """Check that the Mattermost workload is responding to HTTP requests.

    arrange: The charm has been deployed and is active.
    act: Send an HTTP request to the Mattermost unit.
    assert: The response contains 'Mattermost'.
    """

    def is_mattermost_up(status):
        """Return True when all apps are active and Mattermost HTTP responds 200."""
        if not jubilant.all_active(status):
            return False
        try:
            return requests.get(mattermost_address, timeout=10).status_code == 200
        except requests.ConnectionError:
            return False

    juju.wait(is_mattermost_up)
    response = requests.get(mattermost_address, timeout=10)
    assert response.status_code == 200
    assert "Mattermost" in response.text


def test_postgresql_relation(
    app: str,
    juju: jubilant.Juju,
    mattermost_address: str,
):
    """Check that removing and re-adding postgresql relation works correctly.

    arrange: The charm is deployed and active with postgresql integrated.
    act: Remove the postgresql relation, then re-add it.
    assert: The charm goes to waiting/blocked when postgresql is removed,
            and returns to active when re-integrated.
    """

    def is_mattermost_up():
        """Return True when Mattermost HTTP responds 200."""
        try:
            return requests.get(mattermost_address, timeout=10).status_code == 200
        except requests.ConnectionError:
            return False

    def mattermost_connection_fails():
        """Return True when Mattermost HTTP connection fails."""
        try:
            requests.get(mattermost_address, timeout=10)
            return False
        except requests.ConnectionError:
            return True

    def all_active_and_serving(status):
        """All apps are active and Mattermost is serving HTTP responses."""
        return jubilant.all_active(status) and is_mattermost_up()

    # Verify the charm is active and serving before starting
    juju.wait(all_active_and_serving)
    assert is_mattermost_up()

    def postgresql_relation_gone(status):
        """Return True when the postgresql relation is fully removed."""
        relations = status.apps[app].relations
        return "postgresql" not in relations or not relations["postgresql"]

    # Remove the postgresql relation — charm should become waiting/blocked
    juju.remove_relation(app, "postgresql-k8s:database")
    juju.wait(
        lambda status: (status.apps[app].is_waiting or status.apps[app].is_blocked)
        and mattermost_connection_fails()
        and postgresql_relation_gone(status)
    )

    # Re-integrate with postgresql — charm should return to active
    juju.integrate(app, "postgresql-k8s:database")
    juju.wait(all_active_and_serving)
    assert is_mattermost_up()


@pytest.mark.abort_on_fail
def test_s3_storage(
    app: str,
    juju: jubilant.Juju,
    mattermost_address: str,
    s3_address: str | None,
):
    """Check that Mattermost can use S3 for file storage.

    arrange: The charm is deployed and active. MicroCeph radosgw is running
        on the runner host, started by the pre-run script s3-installation.sh.
    act: Deploy s3-integrator, configure it with MicroCeph credentials,
        integrate with mattermost-k8s, create a user, upload a file.
    assert: The file appears in the S3 bucket.
    """
    if not s3_address:
        pytest.skip("requires --s3-address argument or reachable host IP")
        return

    s3_conf = generate_s3_config(s3_address)

    # Deploy and configure s3-integrator
    juju.deploy(
        "s3-integrator",
        channel="latest/edge",
        config={
            "endpoint": s3_conf["endpoint"],
            "bucket": s3_conf["bucket"],
            "path": s3_conf["path"],
            "region": s3_conf["region"],
        },
    )
    juju.wait(lambda status: jubilant.all_blocked(status, "s3-integrator"))

    # Sync S3 credentials via action
    juju.run(
        "s3-integrator/0",
        "sync-s3-credentials",
        {
            "access-key": s3_conf["access-key"],
            "secret-key": s3_conf["secret-key"],
        },
    )
    juju.wait(lambda status: jubilant.all_active(status, "s3-integrator"))

    # Integrate s3-integrator with mattermost-k8s
    juju.integrate(app, "s3-integrator")
    juju.wait(jubilant.all_active, timeout=1200)

    # Create a Mattermost admin user via API
    logger.info("Creating Mattermost admin user for S3 test")
    user_data = {
        "email": "s3test@test.local",
        "username": "s3testuser",
        "password": "S3TestPassword123!",
    }
    response = requests.post(
        f"{mattermost_address}/api/v4/users",
        json=user_data,
        timeout=30,
    )
    assert response.status_code == 201, f"Failed to create user: {response.text}"
    user_id = response.json()["id"]

    # Log in to get auth token
    login_response = requests.post(
        f"{mattermost_address}/api/v4/users/login",
        json={"login_id": user_data["username"], "password": user_data["password"]},
        timeout=30,
    )
    assert login_response.status_code == 200, f"Failed to log in: {login_response.text}"
    token = login_response.headers["Token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a team and channel
    team_response = requests.post(
        f"{mattermost_address}/api/v4/teams",
        headers=headers,
        json={
            "name": "s3testteam",
            "display_name": "S3 Test Team",
            "type": "O",
        },
        timeout=30,
    )
    assert (
        team_response.status_code == 201
    ), f"Failed to create team: {team_response.text}"
    team_id = team_response.json()["id"]

    # Add user to team
    requests.post(
        f"{mattermost_address}/api/v4/teams/{team_id}/members",
        headers=headers,
        json={"team_id": team_id, "user_id": user_id},
        timeout=30,
    )

    # Get the default channel (town-square)
    channels_response = requests.get(
        f"{mattermost_address}/api/v4/teams/{team_id}/channels",
        headers=headers,
        timeout=30,
    )
    assert channels_response.status_code == 200
    channel_id = channels_response.json()[0]["id"]

    # Upload a test file
    logger.info("Uploading test file to Mattermost")
    test_content = b"S3 integration test file content"
    upload_response = requests.post(
        f"{mattermost_address}/api/v4/files",
        headers=headers,
        files={"files": ("s3test.txt", test_content, "text/plain")},
        data={"channel_id": channel_id},
        timeout=30,
    )
    assert (
        upload_response.status_code == 201
    ), f"Failed to upload file: {upload_response.text}"
    file_id = upload_response.json()["file_infos"][0]["id"]

    # Post a message with the file attachment
    post_response = requests.post(
        f"{mattermost_address}/api/v4/posts",
        headers=headers,
        json={
            "channel_id": channel_id,
            "message": "S3 test file",
            "file_ids": [file_id],
        },
        timeout=30,
    )
    assert (
        post_response.status_code == 201
    ), f"Failed to create post: {post_response.text}"

    # Verify the file exists in the S3 bucket
    logger.info("Checking S3 bucket for uploaded file")
    s3 = s3_client_factory(
        "s3",
        region_name=s3_conf["region"],
        aws_access_key_id=s3_conf["access-key"],
        aws_secret_access_key=s3_conf["secret-key"],
        endpoint_url=s3_conf["endpoint"],
        use_ssl=False,
        config=Config(s3={"addressing_style": "path"}),
    )

    bucket_response = s3.list_buckets()
    bucket_names = [b["Name"] for b in bucket_response["Buckets"]]
    assert (
        s3_conf["bucket"] in bucket_names
    ), f"Bucket {s3_conf['bucket']} not found. Buckets: {bucket_names}"

    objects_response = s3.list_objects_v2(Bucket=s3_conf["bucket"])
    assert "Contents" in objects_response, "No objects found in S3 bucket"
    object_count = len(objects_response["Contents"])
    assert object_count > 0, "Expected at least one object in S3 bucket"
    logger.info("Found %d objects in S3 bucket", object_count)

    # Cleanup: remove the s3-integrator relation
    juju.remove_relation(app, "s3-integrator")
    juju.wait(jubilant.all_active, timeout=1200)
