#!/usr/bin/env python3

# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""SMTP integration tests for Mattermost charm."""

import logging

import jubilant
import pytest
import requests

from .conftest import JUJU_WAIT_TIMEOUT, MATTERMOST_PORT

logger = logging.getLogger(__name__)

# Non-routable RFC 5737 TEST-NET-1 address — smtp-integrator becomes active
# without needing a real SMTP server.
_SMTP_HOST = "192.0.2.1"
_SMTP_PORT = 587
_SMTP_DOMAIN = "test.example.com"


def _get_mattermost_address(app: str, juju: jubilant.Juju) -> str:
    """Return a fresh Mattermost HTTP base URL."""
    status = juju.status()
    address = status.apps[app].address or status.apps[app].units[app + "/0"].address
    return f"http://{address}:{MATTERMOST_PORT}"


def _mattermost_up(address: str) -> bool:
    """Return True when Mattermost responds with HTTP 200."""
    try:
        return requests.get(address, timeout=5).status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def _get_admin_token(address: str) -> str:
    """Log in as the pre-created admin user and return an auth token."""
    resp = requests.post(
        f"{address}/api/v4/users/login",
        json={"login_id": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.headers["Token"]


def _get_email_settings(address: str, token: str) -> dict:
    """Return the EmailSettings section of the Mattermost server config.

    Requires a system admin token. Env-var overrides (MM_EMAILSETTINGS_*)
    are reflected in the response without being written back to the database.
    """
    resp = requests.get(
        f"{address}/api/v4/config",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["EmailSettings"]


@pytest.mark.abort_on_fail
def test_smtp_integration(
    app: str,
    juju: jubilant.Juju,
):
    """Check that smtp-integrator passes SMTP env vars to the workload correctly.

    arrange: The charm is deployed and active with postgresql.
    act: Deploy smtp-integrator, configure it, and integrate with mattermost-k8s.
    assert: The charm remains active and the pebble plan for the workload
        service contains the expected SMTP_HOST and SMTP_PORT env vars set
        by paas-charm from the smtp relation data.
    """
    mattermost_address = _get_mattermost_address(app, juju)

    # Wait for HTTP to be ready (app_fixture only waits for Juju active status).
    juju.wait(
        lambda status: jubilant.all_active(status, app)
        and _mattermost_up(mattermost_address),
        timeout=JUJU_WAIT_TIMEOUT,
    )

    # Deploy smtp-integrator
    juju.deploy(
        "smtp-integrator",
        channel="latest/stable",
        config={
            "host": _SMTP_HOST,
            "port": _SMTP_PORT,
            "domain": _SMTP_DOMAIN,
            "transport_security": "none",
            "auth_type": "none",
        },
    )
    juju.wait(
        lambda status: jubilant.all_active(status, "smtp-integrator"),
        timeout=JUJU_WAIT_TIMEOUT,
    )

    juju.integrate(app, "smtp-integrator:smtp")

    juju.wait(
        lambda status: jubilant.all_active(status)
        and _mattermost_up(mattermost_address),
        timeout=JUJU_WAIT_TIMEOUT,
    )
    logger.info("Mattermost is active after SMTP integration")

    # Verify via pebble plan — no Mattermost user or auth required.
    # paas-charm writes SMTP_* env vars into the pebble service layer;
    # the charm container (where juju exec runs) can read the plan via the
    # shared pebble socket.
    task = juju.exec(
        "PEBBLE_SOCKET=/charm/containers/app/pebble.socket pebble plan",
        unit=f"{app}/0",
    )
    plan = task.stdout
    logger.info("Pebble plan:\n%s", plan)

    assert (
        f"SMTP_HOST: {_SMTP_HOST}" in plan
    ), f"Expected SMTP_HOST: {_SMTP_HOST} in pebble plan, got:\n{plan}"
    assert (
        str(_SMTP_PORT) in plan
    ), f"Expected SMTP_PORT {_SMTP_PORT} in pebble plan, got:\n{plan}"
