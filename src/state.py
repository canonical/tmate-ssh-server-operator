# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server states."""
import dataclasses
import ipaddress
import typing

import ops

SSH_DEBUG_INTEGRATION_NAME = "ssh-debug"

@dataclasses.dataclass(frozen=True)
class State:
    """The tmate-ssh-server operator charm state.

    Attributes:
        ip_addr: The host IP address of the given tmate-ssh-server unit.
    """

    ip_addr: typing.Union[ipaddress.IPv4Address, ipaddress.IPv6Address, str, None]

    @classmethod
    def from_charm(cls, charm: ops.CharmBase) -> "State":
        """Initialize the state from charm.

        Args:
            charm: The charm root TmateSSHServer charm.

        Returns:
            The current state of tmate-ssh-server charm.
        """
        # This is to avoid the None type.
        assert (binding := charm.model.get_binding("juju-info"))  # nosec
        return cls(ip_addr=binding.network.bind_address)
