# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://ops.readthedocs.io/en/latest/explanation/testing.html

"""Unit tests for actions."""

import ops
import ops.testing
import pytest

from charm import MattermostK8sCharm

SOCKET_PATH = "/var/tmp/mattermost_local.socket"

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
    "grant-admin-role": {
        "description": "Grant the system_admin role to a specified user.",
        "params": {"user": {"type": "string"}},
    },
    "rotate-secret-key": {"description": "Rotate the secret key."},
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


@pytest.fixture
def context():
    return ops.testing.Context(
        charm_type=MattermostK8sCharm,
        meta=CHARM_META,
        actions=CHARM_ACTIONS,
        config=CHARM_CONFIG,
    )


def test_grant_admin_role_success(context):
    """Test the grant-admin-role action with a successful mmctl execution."""
    user = "valid_user"
    mock_socket_check = ops.testing.Exec(
        command_prefix=["test", "-S", SOCKET_PATH], return_code=0
    )
    mock_mmctl = ops.testing.Exec(
        command_prefix=["/app/bin/mmctl", "--local", "roles", "system-admin", user],
        return_code=0,
        stdout=f"Successfully granted admin role to user {user}",
    )
    container = ops.testing.Container(
        name="app", can_connect=True, execs=[mock_socket_check, mock_mmctl]
    )
    state_in = ops.testing.State(containers=[container])
    action_event = context.on.action("grant-admin-role", params={"user": user})
    state_out = context.run(action_event, state_in)

    assert (
        context.action_results["output"]
        == f"Successfully granted admin role to user {user}"
    )
    plan = state_out.get_container("app").plan
    env = plan.services["go"].environment
    assert env["MM_SERVICESETTINGS_ENABLELOCALMODE"] == "false"


def test_grant_admin_role_exec_error(context):
    """Test the grant-admin-role action with an unsuccessful mmctl execution."""
    user = "invalid_user"
    mock_socket_check = ops.testing.Exec(
        command_prefix=["test", "-S", SOCKET_PATH],
        return_code=0,
    )
    mock_mmctl = ops.testing.Exec(
        command_prefix=["/app/bin/mmctl", "--local", "roles", "system-admin", user],
        return_code=1,
        stderr=f"Error: unable to find user {user}",
    )
    container = ops.testing.Container(
        name="app", can_connect=True, execs=[mock_socket_check, mock_mmctl]
    )
    state_in = ops.testing.State(containers=[container])
    action_event = context.on.action("grant-admin-role", params={"user": user})

    with pytest.raises(ops.testing.ActionFailed) as exc:
        context.run(action_event, state_in)
    assert (
        f"Failed to grant admin role to user {user}: Error: unable to find user {user}"
        in exc.value.message
    )
    state_out = exc.value.state
    plan = state_out.get_container("app").plan
    env = plan.services["go"].environment
    assert env["MM_SERVICESETTINGS_ENABLELOCALMODE"] == "false"


def test_grant_admin_role_socket_timeout(context):
    """Test that the action fails if the socket does not initialize within the timeout period."""
    user = "valid_user"
    mock_socket_fail = ops.testing.Exec(
        command_prefix=["test", "-S", SOCKET_PATH], return_code=1
    )
    container = ops.testing.Container(
        name="app", can_connect=True, execs=[mock_socket_fail]
    )
    state_in = ops.testing.State(containers=[container])
    action_event = context.on.action("grant-admin-role", params={"user": user})
    with pytest.raises(ops.testing.ActionFailed) as exc:
        context.run(action_event, state_in)
    assert (
        "Mattermost socket failed to initialize after 30 seconds" in exc.value.message
    )
