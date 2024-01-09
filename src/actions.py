# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm actions."""
import logging

import ops

import tmate
from state import State

logger = logging.getLogger(__name__)


class Observer(ops.Object):
    """Tmate-ssh-server charm actions observer."""

    def __init__(self, charm: ops.CharmBase, state: State):
        """Initialize the observer and register actions handlers.

        Args:
            charm: The parent charm to attach the observer to.
            state: The charm state.
        """
        super().__init__(charm, "actions-observer")
        self.charm = charm
        self.state = state

        charm.framework.observe(charm.on.get_server_config_action, self.on_get_server_config)

    def on_get_server_config(self, event: ops.ActionEvent) -> None:
        """Get server configuration values for .tmate.conf.

        Args:
            event: The get-server-config action event.
        """
        if not self.state.ip_addr:
            event.fail("Host address not ready yet.")
            return
        try:
            conf = tmate.generate_tmate_conf(str(self.state.ip_addr))
        except tmate.FingerprintError as exc:
            logger.error("Failed to generate .tmate.conf, %s.", exc)
            event.fail("Failed to generate .tmate.conf. See juju debug-log output.")
            return
        event.set_results({"tmate-config": conf})
