#!/usr/bin/env python3

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm Jenkins."""

import logging
import typing

import ops

import tmate
from state import TMATE_SSH_SERVER_SERVICE_NAME

if typing.TYPE_CHECKING:
    from ops.pebble import LayerDict  # pragma: no cover


logger = logging.getLogger(__name__)


class TmateSSHServerK8sOperatorCharm(ops.CharmBase):
    """Charm tmate-ssh-server."""

    def __init__(self, *args: typing.Any):
        """Initialize the charm and register event handlers.

        Args:
            args: Arguments to initialize the charm base.

        Raises:
            RuntimeError: if invalid state value was encountered from relation.
        """
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(
            self.on.tmate_ssh_server_pebble_ready, self._on_tmate_ssh_server_pebble_ready
        )

    def _get_pebble_layer(self) -> ops.pebble.Layer:
        """Return a dictionary representing a Pebble layer.

        Returns:
            The pebble layer defining tmate-ssh-server service layer.
        """
        layer: LayerDict = {
            "summary": "tmate-ssh-server layer",
            "description": "pebble config layer for tmate-ssh-server",
            "services": {
                TMATE_SSH_SERVER_SERVICE_NAME: {
                    "override": "replace",
                    "summary": "tmate-ssh-server",
                    "command": f"./tmate-ssh-server -p {tmate.SSH_PORT} -h 0.0.0.0",
                    "working-dir": str(tmate.EXECUTABLE_DIR),
                    "startup": "enabled",
                    "user": tmate.USER,
                    "group": tmate.GROUP,
                },
            },
            "checks": {
                "online": {
                    "override": "replace",
                    "level": "ready",
                    "tcp": {"port": tmate.SSH_PORT},
                    "period": "30s",
                    "threshold": 5,
                }
            },
        }
        return ops.pebble.Layer(layer)

    def _on_tmate_ssh_server_pebble_ready(self, event: ops.PebbleReadyEvent) -> None:
        """Configure and start Jenkins server.

        Args:
            event: The event fired when pebble is ready.
        """
        container = self.unit.get_container(TMATE_SSH_SERVER_SERVICE_NAME)
        if not container or not container.can_connect():
            self.unit.status = ops.WaitingStatus("Waiting for container.")
            # tmate-ssh-server instantiation should be retried until preconditions are met.
            event.defer()
            return

        self.unit.status = ops.MaintenanceStatus("Starting tmate-ssh-server.")
        container.add_layer(
            TMATE_SSH_SERVER_SERVICE_NAME,
            self._get_pebble_layer(),
            combine=True,
        )
        container.replan()
        self.unit.set_ports(tmate.SSH_PORT)
        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(TmateSSHServerK8sOperatorCharm)
