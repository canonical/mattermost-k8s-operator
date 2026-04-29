#!/usr/bin/env python3
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Go Charm entrypoint."""

import logging
import typing

import ops
import paas_charm.go

from ops.pebble import ExecError

logger = logging.getLogger(__name__)


class MattermostK8sCharm(paas_charm.go.Charm):
    """Go Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)

        # actions
        self.framework.observe(self.on.grant_admin_role_action, self._on_grant_admin_role_action)

    def _on_grant_admin_role_action(self, event: ops.ActionEvent) -> None:
        """Grant the "system_admin" role to a specified user.

        Args:
            event: Event triggering the grant-admin-role action.
        """
        if not self.config.get("local-mode"):
            event.fail("The 'local-mode' config option must be enabled to use this action.")
            return

        container = self.unit.get_container("app")
        if not container.can_connect():
            event.fail("Unable to connect to container, container is not ready")
            return

        user = event.params.get("user")
        if not user:
            event.fail("User parameter is required.")
            return

        cmd = ["/app/bin/mmctl", "--local", "roles", "system-admin", user]
        try:
            process = container.exec(cmd)
            stdout, _ = process.wait_output()
            msg = (
                f"Ran grant-admin-role for user '{user}'. They will need to log out and log back in "
                "to Mattermost to fully receive their permissions upgrade."
            )
            event.set_results({"info": msg, "output": stdout})
        except ExecError as ex:
            event.fail(f"Failed to grant admin role to user {user}: {ex.stderr}")
            return

if __name__ == "__main__":
    ops.main(MattermostK8sCharm)
