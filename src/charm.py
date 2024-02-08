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
        self.framework.observe(self.on.update_status, self._on_update_status)

    def _on_install(self, event: ops.InstallEvent) -> None:
        """Install and start tmate-ssh-server.

        Args:
            event: The event emitted on install hook.

        Raises:
            DependencyInstallError: if the dependencies required to start charm has failed.
            KeyInstallError: if the ssh-key installation and fingerprint generation failed.
            DaemonError: if the workload daemon was unable to start.
        """
        if not self.state.ip_addr:
            logger.warning("Unit address not assigned.")
            # Try again until unit is assigned an IP address.
            event.defer()
            return

        try:
            self.unit.status = ops.MaintenanceStatus("Installing packages.")
            tmate.install_dependencies(self.state.proxy_config)
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
        except tmate.DaemonError as exc:
            logger.error("Failed to start tmate-ssh-server daemon, %s.", exc)
            raise

        try:
            fingerprints = tmate.get_fingerprints()
        except tmate.IncompleteInitError as exc:
            logger.error("Something went wrong initializing keys, %s.", exc)
            raise

        self.unit.open_port("tcp", tmate.PORT)
        self.sshdebug.update_relation_data(host=str(self.state.ip_addr), fingerprints=fingerprints)
        self.unit.status = ops.ActiveStatus()

    def _on_update_status(self, _: ops.UpdateStatusEvent) -> None:
        """Check the health of the workload and restart if necessary."""
        if not self.state.ip_addr:
            logger.warning("Unit address not assigned. Exit hook.")
            return

        if not tmate.is_running():
            logger.error("tmate-ssh-server is not running. Will restart.")

            tmate.start_daemon(address=str(self.state.ip_addr))

            logger.info("Removing stopped containers.")
            try:
                tmate.remove_stopped_containers()
            except tmate.DockerError:
                logger.exception("Failed to remove stopped containers.")

        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(TmateSSHServerOperatorCharm)
