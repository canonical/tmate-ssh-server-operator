# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Observer module for ssh-debug integration."""
import logging

import ops

import tmate
from state import SSH_DEBUG_INTEGRATION_NAME, State

logger = logging.getLogger(__name__)


class Observer(ops.Object):
    """The ssh-debug integration observer."""

    def __init__(self, charm: ops.CharmBase, state: State):
        """Initialize the observer and register event handlers.

        Args:
            charm: The parent charm to attach the observer to.
        """
        super().__init__(charm, "ssh-debug-observer")
        self.charm = charm
        self.state = state

        charm.framework.observe(
            charm.on[SSH_DEBUG_INTEGRATION_NAME].relation_joined,
            self._on_ssh_debug_relation_joined,
        )

    def _on_ssh_debug_relation_joined(self, event: ops.RelationJoinedEvent):
        """Handle ssh-debug relation joined event.

        Args:
            event: The event fired on ssh-debug relation joined.
        """
        try:
            fingerprints = tmate.get_fingerprints()
        except tmate.FingerPrintError as exc:
            logger.error("Error generating fingerprints, %s.", exc)
            self.charm.unit.status = ops.BlockedStatus("Error generating fingerprints.")
            return

        event.relation.data[self.model.unit].update(
            {
                "host": self.state.ip_addr,
                "port": tmate.PORT,
                "rsa-fingerprint": fingerprints.rsa,
                "ed25519-fingerprint": fingerprints.ed25519,
            }
        )
