#!/usr/bin/env python3

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm Jenkins."""

import logging
import subprocess
import typing

import jinja2
import ops
from charms.operator_libs_linux.v0 import apt

import tmate

logger = logging.getLogger(__name__)


class TmateSSHServerOperatorCharm(ops.CharmBase):
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

    def _on_install(self, _: ops.InstallEvent) -> None:
        """Install and start tmate-ssh-server."""
        try:
            self.unit.status = ops.MaintenanceStatus("Installing packages.")
            tmate.install_dependencies()
            self.unit.status = ops.MaintenanceStatus("Generating keys.")
            tmate.install_keys()
            self.unit.status = ops.MaintenanceStatus("Starting tmate-ssh-server daemon.")
            tmate.start_daemon()
        except tmate.DependencyInstallError as exc:
            logger.error("Failed to install docker package, %s.", exc)
            raise
        except tmate.KeyInstallError as exc:
            logger.error("Failed to install/generate keys, %s.", exc)
            raise
        except tmate.DaemonStartError as exc:
            logger.error("Failed to start tmate-ssh-server daemon, %s.", exc)
            raise

        self.unit.status = ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main.main(TmateSSHServerOperatorCharm)
