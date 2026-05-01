#!/usr/bin/env python3
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Go Charm entrypoint."""

import logging
import time
import typing

import ops
import paas_charm.go
from ops.pebble import ExecError, LayerDict

logger = logging.getLogger(__name__)

SOCKET_PATH = "/var/tmp/mattermost_local.socket"


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

    def _set_local_mode(self, container: ops.Container, enable: bool) -> bool:
        """Toggle local mode via Pebble layer and wait for readiness if enabling.

        Args:
            container: The Pebble container for the app.
            enable: True to enable local mode, False to disable it.

        Returns:
            bool: True if successful, False if the socket fails to initialize on startup.
        """
        layer: LayerDict = {
            "services": {
                "go": {
                    "override": "merge",
                    "environment": {
                        "MM_SERVICESETTINGS_ENABLELOCALMODE": ("true" if enable else "false")
                    },
                }
            }
        }
        container.add_layer("local-mode-patch", layer, combine=True)
        container.replan()

        if not enable:
            return True

        timeout = 30
        poll_interval = 2
        time_elapsed = 0

        while time_elapsed < timeout:
            try:
                container.exec(["test", "-S", SOCKET_PATH]).wait_output()
                return True
            except ExecError:
                time.sleep(poll_interval)
                time_elapsed += poll_interval
        return False

    def _on_grant_admin_role_action(self, event: ops.ActionEvent) -> None:
        """Grant the "system_admin" role to a specified user.

        Args:
            event: Event triggering the grant-admin-role action.
        """
        container = self.unit.get_container("app")
        if not container.can_connect():
            event.fail("Unable to connect to container, container is not ready")
            return

        user = event.params.get("user")
        if not user:
            event.fail("User parameter is required")
            return

        try:
            if not self._set_local_mode(container, enable=True):
                event.fail("Mattermost socket failed to initialize after 30 seconds")
                return

            cmd = ["/app/bin/mmctl", "--local", "roles", "system-admin", user]
            process = container.exec(cmd)
            stdout, _ = process.wait_output()
            msg = (
                f"Action completed. If user '{user}' was not already a system administrator, "
                "they will need to log out and log back in to fully receive their permissions"
            )
            event.set_results({"info": msg, "output": stdout})
        except ExecError as ex:
            event.fail(f"Failed to grant admin role to user {user}: {ex.stderr}")
        finally:
            self._set_local_mode(container, enable=False)


if __name__ == "__main__":
    ops.main(MattermostK8sCharm)
