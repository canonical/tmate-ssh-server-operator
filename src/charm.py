#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm tmate-ssh-server."""

import logging
import typing

import ops

import actions
import ssh_debug
import tmate
from state import State

logger = logging.getLogger(__name__)


class TmateSSHServerOperatorCharm(ops.CharmBase):
    """Charm tmate-ssh-server."""

    def __init__(self, *args: typing.Any):
        """Initialize the charm and register event handlers.

        Args:
            args: Arguments to initialize the charm base.
        """
        super().__init__(*args)
        self.state = State.from_charm(self)
        self.actions = actions.Observer(self, self.state)
        self.sshdebug = ssh_debug.Observer(self, self.state)

        self.framework.observe(self.on.install, self._on_install)

    def _on_install(self, event: ops.InstallEvent) -> None:
        """Install and start tmate-ssh-server.

        Args:
            event: The event emitted on install hook.

        Raises:
            DependencyInstallError: if the dependencies required to start charm has failed.
            KeyInstallError: if the ssh-key installation and fingerprint generation failed.
            DaemonStartError: if the workload daemon was unable to start.
        """
        if not self.state.ip_addr:
            logger.warning("Unit address not assigned.")
            # Try again until unit is assigned an IP address.
            event.defer()
            return

        try:
            self.unit.status = ops.MaintenanceStatus("Installing packages.")
            tmate.install_dependencies()
        except tmate.DependencySetupError as exc:
            logger.error("Failed to install docker package, %s.", exc)
            raise

        try:
            self.unit.status = ops.MaintenanceStatus("Generating keys.")
            tmate.install_keys(host_ip=self.state.ip_addr)
        except tmate.KeyInstallError as exc:
            logger.error("Failed to install/generate keys, %s.", exc)
            raise

        try:
            self.unit.status = ops.MaintenanceStatus("Starting tmate-ssh-server daemon.")
            tmate.start_daemon(address=str(self.state.ip_addr))
        except tmate.DaemonStartError as exc:
            logger.error("Failed to start tmate-ssh-server daemon, %s.", exc)
            raise

        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(TmateSSHServerOperatorCharm)
