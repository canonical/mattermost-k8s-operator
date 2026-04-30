#!/usr/bin/env python3

# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""SMTP integration tests for Mattermost charm."""

import logging

import jubilant
import pytest
import requests

from .conftest import ADMIN_PASSWORD, ADMIN_USERNAME, JUJU_WAIT_TIMEOUT, MATTERMOST_PORT

logger = logging.getLogger(__name__)

# Fake SMTP values that won't route anywhere (RFC 5737 TEST-NET-1)
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
    """Check that smtp-integrator configures Mattermost email settings correctly.

    arrange: The charm is deployed and active with postgresql.
    act: Deploy smtp-integrator, configure it, and integrate with mattermost-k8s.
    assert: Mattermost stays active and its public client config reports that
        email notifications are enabled. Env vars in the workload container
        reflect the mapped MM_EMAILSETTINGS_* values.
    """
    mattermost_address = _get_mattermost_address(app, juju)

    # Wait for Mattermost HTTP to be ready before any API calls.
    # The session-scoped app fixture only waits for Juju active status, not for
    # the HTTP port — Mattermost can take additional time to bind.
    juju.wait(
        lambda status: jubilant.all_active(status, app)
        and _mattermost_up(mattermost_address),
        timeout=JUJU_WAIT_TIMEOUT,
    )

    # Deploy smtp-integrator with non-routable TEST-NET-1 address so the
    # charm becomes active without actually connecting to an SMTP server.
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

    # Integrate smtp-integrator with mattermost-k8s
    juju.integrate(app, "smtp-integrator:smtp")

    def all_active_and_mattermost_serving(status):
        if not jubilant.all_active(status):
            return False
        return _mattermost_up(mattermost_address)

    juju.wait(all_active_and_mattermost_serving, timeout=JUJU_WAIT_TIMEOUT)
    logger.info("Mattermost is active after SMTP integration")

    # --- Verify via Mattermost admin API --------------------------------------
    # GET /api/v4/config returns the effective config including MM_EMAILSETTINGS_*
    # env var overrides. Env var values are NOT written back to the database,
    # so they appear here only while the env var is set (i.e. while the SMTP
    # relation is active).
    token = _get_admin_token(mattermost_address)
    email_settings = _get_email_settings(mattermost_address, token)
    logger.info("EmailSettings after SMTP integration: %s", email_settings)

    assert (
        email_settings.get("SMTPServer") == _SMTP_HOST
    ), f"Expected SMTPServer={_SMTP_HOST}, got: {email_settings.get('SMTPServer')}"
    assert str(email_settings.get("SMTPPort", "")) == str(
        _SMTP_PORT
    ), f"Expected SMTPPort={_SMTP_PORT}, got: {email_settings.get('SMTPPort')}"
    assert (
        email_settings.get("SendEmailNotifications") is True
    ), f"Expected SendEmailNotifications=true, got: {email_settings.get('SendEmailNotifications')}"
    # auth_type=none → EnableSMTPAuth must be false
    assert (
        email_settings.get("EnableSMTPAuth") is False
    ), f"Expected EnableSMTPAuth=false, got: {email_settings.get('EnableSMTPAuth')}"


@pytest.mark.abort_on_fail
def test_smtp_removal(
    app: str,
    juju: jubilant.Juju,
):
    """Check that removing the SMTP relation disables email notifications.

    arrange: The smtp-integrator is integrated with mattermost-k8s.
    act: Remove the smtp relation.
    assert: Mattermost returns to active and email notifications are disabled.
    """
    mattermost_address = _get_mattermost_address(app, juju)

    juju.remove_relation(app, "smtp-integrator")

    def all_active_and_mattermost_serving(status):
        if not jubilant.all_active(status):
            return False
        return _mattermost_up(mattermost_address)

    juju.wait(all_active_and_mattermost_serving, timeout=JUJU_WAIT_TIMEOUT)
    logger.info("Mattermost is active after SMTP removal")

    # Re-login (Mattermost may have restarted, invalidating the previous token).
    # MM_EMAILSETTINGS_* env vars are no longer passed by start.sh, so Mattermost
    # falls back to its database defaults (empty SMTPServer, notifications off).
    # Env var overrides are never written back to the DB, so these defaults hold.
    token = _get_admin_token(mattermost_address)
    email_settings = _get_email_settings(mattermost_address, token)
    logger.info("EmailSettings after SMTP removal: %s", email_settings)

    assert email_settings.get("SendEmailNotifications") is False, (
        "Expected SendEmailNotifications=false after SMTP removal, "
        f"got: {email_settings.get('SendEmailNotifications')}"
    )
    assert email_settings.get("SMTPServer") == "", (
        f"Expected SMTPServer to be empty after SMTP removal, "
        f"got: {email_settings.get('SMTPServer')}"
    )
    logger.info("Email settings correctly reverted to defaults after SMTP removal")
