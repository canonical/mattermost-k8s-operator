# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://ops.readthedocs.io/en/latest/explanation/testing.html

"""Unit tests."""

import ops
import ops.testing

from charm import MattermostK8sCharm

# Metadata from the go-framework extension (charmcraft expand-extensions).
# Needed because Scenario cannot expand charmcraft extensions automatically.
CHARM_META = {
    "name": "mattermost-k8s",
    "containers": {"app": {"resource": "app-image"}},
    "peers": {"secret-storage": {"interface": "secret-storage"}},
    "requires": {
        "postgresql": {"interface": "postgresql_client", "optional": False, "limit": 1},
        "logging": {"interface": "loki_push_api"},
        "ingress": {"interface": "ingress", "limit": 1},
    },
    "provides": {
        "metrics-endpoint": {"interface": "prometheus_scrape"},
        "grafana-dashboard": {"interface": "grafana_dashboard"},
    },
    "resources": {"app-image": {"type": "oci-image"}},
}

CHARM_ACTIONS = {
    "rotate-secret-key": {
        "description": "Rotate the secret key.",
    },
}

CHARM_CONFIG = {
    "options": {
        "app-port": {
            "type": "int",
            "default": 8080,
            "description": "Default port where the application will listen on.",
        },
        "metrics-port": {
            "type": "int",
            "default": 8080,
            "description": "Port where the prometheus metrics will be scraped.",
        },
        "metrics-path": {
            "type": "string",
            "default": "/metrics",
            "description": "Path where the prometheus metrics will be scraped.",
        },
        "app-secret-key": {
            "type": "string",
            "description": "Secret key for sessions.",
        },
        "app-secret-key-id": {
            "type": "secret",
            "description": "Juju user secret ID for the app secret key.",
        },
    },
}


def test_container_not_ready():
    """
    arrange: State with the container app that cannot connect.
    act: Run config_changed hook.
    assert: The unit is waiting for Pebble.
    """
    context = ops.testing.Context(
        charm_type=MattermostK8sCharm,
        meta=CHARM_META,
        actions=CHARM_ACTIONS,
        config=CHARM_CONFIG,
    )
    container = ops.testing.Container(name="app", can_connect=False)
    state_in = ops.testing.State(
        containers={container},
    )
    state_out = context.run(context.on.config_changed(), state_in)
    assert state_out.unit_status == ops.testing.WaitingStatus(
        "Waiting for pebble ready"
    )


def test_missing_postgresql_integration():
    """
    arrange: State with the container ready and peer relation, but no postgresql.
    act: Run pebble_ready hook.
    assert: The unit is blocked due to missing postgresql integration.
    """
    context = ops.testing.Context(
        charm_type=MattermostK8sCharm,
        meta=CHARM_META,
        actions=CHARM_ACTIONS,
        config=CHARM_CONFIG,
    )
    container = ops.testing.Container(name="app", can_connect=True)
    peer = ops.testing.PeerRelation(
        endpoint="secret-storage",
        local_app_data={"go_secret_key": "test-secret-key"},
    )
    state_in = ops.testing.State(
        leader=True,
        containers={container},
        relations={peer},
    )
    state_out = context.run(context.on.pebble_ready(container), state_in)
    assert state_out.unit_status.name == "blocked"


def test_missing_peer_relation():
    """
    arrange: State with the container ready but no peer relation.
    act: Run pebble_ready hook.
    assert: The unit is waiting for the peer integration.
    """
    context = ops.testing.Context(
        charm_type=MattermostK8sCharm,
        meta=CHARM_META,
        actions=CHARM_ACTIONS,
        config=CHARM_CONFIG,
    )
    container = ops.testing.Container(name="app", can_connect=True)
    state_in = ops.testing.State(
        containers={container},
    )
    state_out = context.run(context.on.pebble_ready(container), state_in)
    assert state_out.unit_status == ops.testing.WaitingStatus(
        "Waiting for peer integration"
    )
