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

    # --- Verify MM_EMAILSETTINGS_* env vars in the workload container ---------
    # The public /api/v4/config/client endpoint does not expose email settings
    # (those require admin auth). Instead read the mattermost process environ
    # directly via /proc to confirm start.sh mapped SMTP_* → MM_EMAILSETTINGS_*.
    ssh_output = juju.ssh(
        f"{app}/0",
        "cat /proc/*/environ 2>/dev/null | tr '\\0' '\\n' | grep '^MM_EMAILSETTINGS_' | sort -u",
        container="app",
    )
    logger.info("MM_EMAILSETTINGS env vars in container:\n%s", ssh_output)
    assert (
        f"MM_EMAILSETTINGS_SMTPSERVER={_SMTP_HOST}" in ssh_output
    ), f"Expected MM_EMAILSETTINGS_SMTPSERVER={_SMTP_HOST} in env, got:\n{ssh_output}"
    assert (
        f"MM_EMAILSETTINGS_SMTPPORT={_SMTP_PORT}" in ssh_output
    ), f"Expected MM_EMAILSETTINGS_SMTPPORT={_SMTP_PORT} in env, got:\n{ssh_output}"
    assert (
        "MM_EMAILSETTINGS_SENDEMAILNOTIFICATIONS=true" in ssh_output
    ), f"Expected MM_EMAILSETTINGS_SENDEMAILNOTIFICATIONS=true in env, got:\n{ssh_output}"
    assert f"MM_EMAILSETTINGS_FEEDBACKEMAIL=noreply@{_SMTP_DOMAIN}" in ssh_output, (
        f"Expected MM_EMAILSETTINGS_FEEDBACKEMAIL=noreply@{_SMTP_DOMAIN} in env, "
        f"got:\n{ssh_output}"
    )


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

    # Verify that MM_EMAILSETTINGS_SMTPSERVER is no longer present in the
    # mattermost process environment after the relation is removed.
    ssh_after_removal = juju.ssh(
        f"{app}/0",
        "cat /proc/*/environ 2>/dev/null | tr '\\0' '\\n' | grep '^MM_EMAILSETTINGS_SMTPSERVER=' || true",
        container="app",
    )
    assert not ssh_after_removal.strip(), (
        "Expected MM_EMAILSETTINGS_SMTPSERVER to be unset after SMTP removal, "
        f"got: {ssh_after_removal}"
    )
    logger.info("SMTP env vars correctly absent after relation removal")
