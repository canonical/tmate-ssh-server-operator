# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Factories for generating test data."""

# The factory definitions don't need public methods
# pylint: disable=too-few-public-methods

from typing import Generic, TypeVar

import factory

from state import ProxyConfig, State

T = TypeVar("T")


class BaseMetaFactory(Generic[T], factory.base.FactoryMetaClass):
    """Used for type hints of factories."""

    # No need for docstring because it is used for type hints
    def __call__(cls, *args, **kwargs) -> T:  # noqa: N805
        """Used for type hints of factories."""  # noqa: DCO020
        return super().__call__(*args, **kwargs)  # noqa: DCO030


# The attributes of these classes are generators for the attributes of the meta class
# mypy incorrectly believes the factories don't support metaclass
class ProxyConfigFactory(factory.Factory, metaclass=BaseMetaFactory[ProxyConfig]):  # type: ignore
    # Docstrings have been abbreviated for factories, checking for docstrings on model attributes
    # can be skipped.
    """Generate PathInfos."""  # noqa: DCO060

    class Meta:
        """Configuration for factory."""  # noqa: DCO060

        model = ProxyConfig
        abstract = False

    http_proxy = "http://proxy.address:3128"
    https_proxy = "https://proxy.address:3128"
    no_proxy = "http://hello.org,http://goodbye.org"


# The attributes of these classes are generators for the attributes of the meta class
# mypy incorrectly believes the factories don't support metaclass
class StateFactory(factory.Factory, metaclass=BaseMetaFactory[State]):  # type: ignore[misc]
    # Docstrings have been abbreviated for factories, checking for docstrings on model attributes
    # can be skipped.
    """Generate PathInfos."""  # noqa: DCO060

    class Meta:
        """Configuration for factory."""  # noqa: DCO060

        model = State
        abstract = False

    ip_addr = factory.Faker("ipv4")
    proxy_config = factory.SubFactory(ProxyConfigFactory)
