#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more at: https://documentation.ubuntu.com/juju/3.6/howto/manage-charms/#build-a-charm

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

https://discourse.charmhub.io/t/4208
"""

import logging
import typing

import ops
from ops import pebble

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

VALID_LOG_LEVELS = ["info", "debug", "warning", "error", "critical"]


class Charm(ops.CharmBase):
    """Charm implementing holistic reconciliation pattern.

    The holistic pattern centralizes all state reconciliation logic into a single
    reconcile method that is called from all event handlers. This ensures consistency
    and reduces code duplication.
    See https://documentation.ubuntu.com/ops/latest/explanation/holistic-vs-delta-charms/
    for more information.
    """

    def __init__(self, *args: typing.Any):
        """Construct.

        Args:
            args: Arguments passed to the CharmBase parent constructor.
        """
        super().__init__(*args)
        self.framework.observe(self.on.httpbin_pebble_ready, self._on_httpbin_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def reconcile(self) -> None:
        """Holistic reconciliation method.

        This method contains all the logic needed to reconcile the charm state.
        It is idempotent and can be called from any event handler.

        Learn more about interacting with Pebble at
        https://documentation.ubuntu.com/juju/3.6/reference/pebble/
        """
        # Validate configuration
        log_level = str(self.model.config["log-level"]).lower()
        if log_level not in VALID_LOG_LEVELS:
            self.unit.status = ops.BlockedStatus(f"invalid log level: '{log_level}'")
            return

        # Get container
        container = self.unit.get_container("httpbin")
        if not container.can_connect():
            self.unit.status = ops.WaitingStatus("waiting for Pebble API")
            return

        # Configure and ensure workload is running
        container.add_layer("httpbin", self._pebble_layer, combine=True)
        container.replan()

        logger.debug("Workload reconciled with log level: %s", log_level)
        # Learn more about statuses in the SDK docs:
        # https://documentation.ubuntu.com/juju/latest/reference/status/index.html
        self.unit.status = ops.ActiveStatus()

    def _on_httpbin_pebble_ready(self, _: ops.PebbleReadyEvent) -> None:
        """Handle httpbin pebble ready event."""
        self.reconcile()

    def _on_config_changed(self, _: ops.ConfigChangedEvent) -> None:
        """Handle changed configuration."""
        self.reconcile()

    @property
    def _pebble_layer(self) -> pebble.LayerDict:
        """Return a dictionary representing a Pebble layer."""
        return {
            "summary": "httpbin layer",
            "description": "pebble config layer for httpbin",
            "services": {
                "httpbin": {
                    "override": "replace",
                    "summary": "httpbin",
                    "command": "gunicorn -b 0.0.0.0:80 httpbin:app -k gevent",
                    "startup": "enabled",
                    "environment": {
                        "GUNICORN_CMD_ARGS": f"--log-level {self.model.config['log-level']}"
                    },
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    ops.main(Charm)
