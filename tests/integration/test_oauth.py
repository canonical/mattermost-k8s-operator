#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""OAuth integration tests for Mattermost charm."""

import logging

import jubilant
import pytest

from .conftest import JUJU_WAIT_TIMEOUT

logger = logging.getLogger(__name__)


def _ensure_deployed(juju: jubilant.Juju, app_name: str, **kwargs):
    """Deploy a charm only if it is not already present in the model.

    Args:
        juju: Jubilant Juju client.
        app_name: Application name to check / deploy as.
        kwargs: Extra keyword arguments forwarded to ``juju.deploy``.
    """
    if app_name in juju.status().apps:
        logger.info("%s already deployed, skipping", app_name)
        return
    juju.deploy(app_name, **kwargs)


def _safe_integrate(juju: jubilant.Juju, endpoint1: str, endpoint2: str):
    """Create a Juju relation, ignoring errors if it already exists.

    Args:
        juju: Jubilant Juju client.
        endpoint1: First endpoint (e.g. "app:relation").
        endpoint2: Second endpoint.
    """
    try:
        juju.integrate(endpoint1, endpoint2)
    except jubilant.CLIError:
        logger.info("Integration %s <-> %s may already exist", endpoint1, endpoint2)


def _deploy_identity_platform(juju: jubilant.Juju):
    """Deploy the Canonical identity platform stack (hydra, kratos, login-ui).

    Wires the identity platform to the existing postgresql-k8s and traefik-k8s
    applications already present in the model.

    Args:
        juju: Jubilant Juju client.
    """
    _ensure_deployed(juju, "hydra", channel="latest/edge", trust=True)
    _ensure_deployed(juju, "kratos", channel="latest/edge", trust=True)
    _ensure_deployed(
        juju,
        "identity-platform-login-ui-operator",
        channel="latest/edge",
        trust=True,
    )

    # Identity platform → postgresql
    _safe_integrate(juju, "postgresql-k8s:database", "hydra:pg-database")
    _safe_integrate(juju, "postgresql-k8s:database", "kratos:pg-database")

    # Internal identity platform wiring
    _safe_integrate(juju, "hydra:hydra-endpoint-info", "kratos:hydra-endpoint-info")
    _safe_integrate(
        juju,
        "hydra:hydra-endpoint-info",
        "identity-platform-login-ui-operator:hydra-endpoint-info",
    )
    _safe_integrate(
        juju,
        "hydra:ui-endpoint-info",
        "identity-platform-login-ui-operator:ui-endpoint-info",
    )
    _safe_integrate(
        juju,
        "kratos:ui-endpoint-info",
        "identity-platform-login-ui-operator:ui-endpoint-info",
    )
    _safe_integrate(
        juju,
        "kratos:kratos-info",
        "identity-platform-login-ui-operator:kratos-info",
    )

    # Identity platform → traefik (public routes)
    _safe_integrate(juju, "traefik-k8s:traefik-route", "hydra:public-route")
    _safe_integrate(juju, "traefik-k8s:traefik-route", "kratos:public-route")
    _safe_integrate(
        juju,
        "traefik-k8s:traefik-route",
        "identity-platform-login-ui-operator:public-route",
    )

    juju.config("kratos", {"enforce_mfa": False})


@pytest.mark.abort_on_fail
def test_oauth_integration(
    app: str,
    juju: jubilant.Juju,
):
    """Check that the oauth integration passes OAuth env vars to the workload.

    arrange: The charm is deployed and active with postgresql.
    act: Deploy traefik for ingress (required by paas-charm for OAuth),
         deploy the identity platform (hydra, kratos, login-ui),
         and integrate mattermost:oauth with hydra.
    assert: The pebble plan for the workload service contains the expected
        APP_OAUTH_* env vars set by paas-charm from the oauth relation data.
    """
    # Deploy traefik for ingress — paas-charm requires ingress to build the
    # OAuth redirect URI that is registered with the identity provider.
    _ensure_deployed(
        juju,
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
        timeout=JUJU_WAIT_TIMEOUT,
    )

    # TLS on traefik (needed by identity platform OIDC endpoints)
    _safe_integrate(
        juju, "self-signed-certificates:certificates", "traefik-k8s:certificates"
    )
    # Mattermost ingress via traefik
    _safe_integrate(juju, f"{app}:ingress", "traefik-k8s:ingress")
    juju.wait(jubilant.all_active, timeout=JUJU_WAIT_TIMEOUT)

    # Deploy the full identity platform stack
    _deploy_identity_platform(juju)
    juju.wait(
        lambda status: jubilant.all_active(
            status, "hydra", "kratos", "identity-platform-login-ui-operator"
        ),
        timeout=JUJU_WAIT_TIMEOUT,
    )

    # Integrate mattermost with hydra for OAuth/OIDC
    _safe_integrate(juju, f"{app}:oauth", "hydra")
    juju.wait(jubilant.all_active, timeout=JUJU_WAIT_TIMEOUT)

    # Verify OAuth env vars are present in the pebble plan.
    # paas-charm writes APP_OAUTH_* env vars into the pebble service layer;
    # start.sh then translates them to MM_OPENIDSETTINGS_* at runtime.
    task = juju.exec(
        "PEBBLE_SOCKET=/charm/containers/app/pebble.socket pebble plan",
        unit=f"{app}/0",
    )
    plan = task.stdout
    logger.info("Pebble plan:\n%s", plan)

    assert (
        "APP_OAUTH_CLIENT_ID" in plan
    ), f"Expected APP_OAUTH_CLIENT_ID in pebble plan, got:\n{plan}"
    assert (
        "APP_OAUTH_CLIENT_SECRET" in plan
    ), f"Expected APP_OAUTH_CLIENT_SECRET in pebble plan, got:\n{plan}"
    assert (
        "APP_OAUTH_API_BASE_URL" in plan
    ), f"Expected APP_OAUTH_API_BASE_URL in pebble plan, got:\n{plan}"
