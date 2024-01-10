# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server states."""
import dataclasses
import ipaddress
import typing

import ops

DEBUG_SSH_INTEGRATION_NAME = "debug-ssh"


class CharmStateBaseError(Exception):
    """Represents an error with charm state."""


class InvalidCharmStateError(CharmStateBaseError):
    """Represents an invalid charm state."""

    def __init__(self, reason: str):
        """Initialize the error.

        Args:
            reason: The reason why the state is invalid.
        """
        self.reason = reason


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

        Raises:
            InvalidCharmStateError: if the network bind address was not of IPv4/IPv6.
        """
        binding = charm.model.get_binding("juju-info")
        if not binding:
            return cls(ip_addr=None)
        # If unable to get a casted IPvX address, it is not useful.
        # https://github.com/canonical/operator/blob/8a08e8e1b389fce4e7b54663863c4b2d06e72224/ops/model.py#L939-L947
        if isinstance(binding.network.bind_address, str):
            raise InvalidCharmStateError(
                f"Invalid network bind address {binding.network.bind_address}."
            )
        return cls(ip_addr=binding.network.bind_address if binding else None)
