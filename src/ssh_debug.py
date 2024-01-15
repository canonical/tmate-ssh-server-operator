# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Observer module for ssh-debug integration."""
import logging
import typing

import ops

import tmate
from state import DEBUG_SSH_INTEGRATION_NAME, State

logger = logging.getLogger(__name__)


class Observer(ops.Object):
    """The ssh-debug integration observer."""

    def __init__(self, charm: ops.CharmBase, state: State):
        """Initialize the observer and register event handlers.

        Args:
            charm: The parent charm to attach the observer to.
            state: The charm state.
        """
        super().__init__(charm, "ssh-debug-observer")
        self.charm = charm
        self.state = state

        charm.framework.observe(
            charm.on[DEBUG_SSH_INTEGRATION_NAME].relation_joined,
            self._on_ssh_debug_relation_joined,
        )

    def update_relation_data(self, host: str, fingerprints: tmate.Fingerprints) -> None:
        """Update ssh_debug relation data if relation is available.

        Args:
            host: The unit's bound IP address.
            fingerprints: The tmate-ssh-server generated fingerprint for RSA and ED25519 keys.
        """
        relations: typing.List[ops.Relation] | None = self.charm.model.relations.get(
            DEBUG_SSH_INTEGRATION_NAME
        )
        if not relations:
            logger.warning(
                "%s relation not yet ready. Relation data will be setup when it becomes available.",
                DEBUG_SSH_INTEGRATION_NAME,
            )
            return
        for relation in relations:
            relation_data: ops.RelationDataContent = relation.data[self.charm.unit]
            relation_data.update(
                {
                    "host": host,
                    "port": str(tmate.PORT),
                    "rsa_fingerprint": fingerprints.rsa,
                    "ed25519_fingerprint": fingerprints.ed25519,
                }
            )

    def _on_ssh_debug_relation_joined(self, _: ops.RelationJoinedEvent) -> None:
        """Handle ssh-debug relation joined event.

        Raises:
            KeyInstallError: if there was an error getting keys fingerprints.
        """
        try:
            fingerprints = tmate.get_fingerprints()
        except tmate.IncompleteInitError as exc:
            logger.error("Error getting fingerprint data, %s.", exc)
            raise

        self.update_relation_data(host=str(self.state.ip_addr), fingerprints=fingerprints)
