#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for Mattermost charm."""

import logging

import jubilant
import pytest
import requests

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
def test_ingress(
    app: str,
    juju: jubilant.Juju,
):
    """Check that integrating traefik-k8s provides a reachable ingress URL.

    arrange: The charm is deployed and active with postgresql.
    act: Deploy traefik-k8s with subdomain routing, integrate with mattermost-k8s.
    assert: The ingress URL from the relation data is reachable and serves Mattermost.
    """
    juju.deploy(
        "traefik-k8s",
        channel="latest/stable",
        trust=True,
        config={
            "routing_mode": "subdomain",
            "external_hostname": "testing.local",
        },
    )
    juju.wait(
        lambda status: jubilant.all_active(status, "traefik-k8s"),
        timeout=1200,
    )

    juju.integrate(f"{app}:ingress", "traefik-k8s:ingress")
    juju.wait(jubilant.all_active, timeout=1200)

    # The ingress relation should now have a URL.
    # Use the traefik unit's pod IP (not the app ClusterIP which is on port 65535).
    status = juju.status()
    traefik_unit_address = status.apps["traefik-k8s"].units["traefik-k8s/0"].address

    # With subdomain routing, traefik routes based on Host header.
    model = juju.model
    ingress_host = f"{model}-{app}.testing.local"
    response = requests.get(
        f"http://{traefik_unit_address}",
        headers={"Host": ingress_host},
        timeout=10,
    )
    assert response.status_code == 200
    assert "Mattermost" in response.text
    logger.info(
        "Ingress test passed: Mattermost reachable via traefik at %s", ingress_host
    )
