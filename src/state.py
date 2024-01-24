# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server states."""
import dataclasses
import ipaddress
import logging
import os
import typing

import ops
from pydantic import BaseModel, HttpUrl, ValidationError

logger = logging.getLogger(__name__)

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


class CharmConfigInvalidError(CharmStateBaseError):
    """Exception raised when a charm configuration is found to be invalid.

    Attributes:
        msg: Explanation of the error.
    """

    def __init__(self, msg: str):
        """Initialize a new instance of the CharmConfigInvalidError exception.

        Args:
            msg: Explanation of the error.
        """
        self.msg = msg


class ProxyConfig(BaseModel):
    """Configuration for accessing Jenkins through proxy.

    Attributes:
        http_proxy: The http proxy URL.
        https_proxy: The https proxy URL.
        no_proxy: Comma separated list of hostnames to bypass proxy.
    """

    http_proxy: typing.Optional[HttpUrl]
    https_proxy: typing.Optional[HttpUrl]
    no_proxy: typing.Optional[str]

    @classmethod
    def from_env(cls) -> typing.Optional["ProxyConfig"]:
        """Instantiate ProxyConfig from juju charm environment.

        Returns:
            ProxyConfig if proxy configuration is provided, None otherwise.
        """
        http_proxy = os.environ.get("JUJU_CHARM_HTTP_PROXY")
        https_proxy = os.environ.get("JUJU_CHARM_HTTPS_PROXY")
        no_proxy = os.environ.get("JUJU_CHARM_NO_PROXY")
        if not http_proxy and not https_proxy:
            return None
        # Mypy doesn't understand str is supposed to be converted to HttpUrl by Pydantic.
        return cls(
            http_proxy=http_proxy, https_proxy=https_proxy, no_proxy=no_proxy  # type: ignore
        )


@dataclasses.dataclass(frozen=True)
class State:
    """The tmate-ssh-server operator charm state.

    Attributes:
        ip_addr: The host IP address of the given tmate-ssh-server unit.
        proxy_config: The proxy configuration to apply to services used by tmate.
    """

    ip_addr: typing.Optional[typing.Union[ipaddress.IPv4Address, ipaddress.IPv6Address, str]]
    proxy_config: typing.Optional[ProxyConfig]

    @classmethod
    def from_charm(cls, charm: ops.CharmBase) -> "State":
        """Initialize the state from charm.

        Args:
            charm: The charm root TmateSSHServer charm.

        Returns:
            The current state of tmate-ssh-server charm.

        Raises:
            InvalidCharmStateError: if the network bind address was not of IPv4/IPv6.
            CharmConfigInvalidError: if there was something wrong with charm configuration values.
        """
        try:
            proxy_config = ProxyConfig.from_env()
        except ValidationError as exc:
            logger.error("Invalid juju model proxy configuration, %s", exc)
            raise CharmConfigInvalidError("Invalid model proxy configuration.") from exc

        binding = charm.model.get_binding("juju-info")
        if not binding:
            return cls(ip_addr=None, proxy_config=proxy_config)
        # If unable to get a casted IPvX address, it is not useful.
        # https://github.com/canonical/operator/blob/8a08e8e1b389fce4e7b54663863c4b2d06e72224/ops/model.py#L939-L947
        if isinstance(binding.network.bind_address, str):
            raise InvalidCharmStateError(
                f"Invalid network bind address {binding.network.bind_address}."
            )

        return cls(
            ip_addr=binding.network.bind_address if binding else None, proxy_config=proxy_config
        )
