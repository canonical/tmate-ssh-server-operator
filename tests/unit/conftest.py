# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for tmate-ssh-server-operator charm unit tests."""

from unittest.mock import MagicMock

import pytest
from ops.testing import Harness

import tmate
from charm import TmateSSHServerOperatorCharm
from tmate import Fingerprints


@pytest.fixture(scope="function", name="harness")
def harness_fixture():
    """Enable ops test framework harness."""
    harness = Harness(TmateSSHServerOperatorCharm)
    # The charm code `binding.network.bind_address` for getting unit ip address will fail without
    # the add_network call.
    harness.add_network("10.0.0.10")
    yield harness
    harness.cleanup()


@pytest.fixture(scope="function", name="charm")
def charm_fixture(harness: Harness):
    """Harnessed TmateSSHServerOperator charm."""
    harness.begin()
    return harness.charm


@pytest.fixture(scope="function", name="fingerprints")
def fingerprints_fixture():
    """Test fingerprint fixture."""
    return Fingerprints(rsa="rsa_fingerprint", ed25519="ed25519_fingerprint")


@pytest.fixture(scope="function", name="patch_get_fingerprints")
def patch_get_fingerprints_fixture(monkeypatch: pytest.MonkeyPatch, fingerprints: Fingerprints):
    """Monkeypatch get_fingerprints function."""
    monkeypatch.setattr(
        tmate,
        "get_fingerprints",
        MagicMock(spec=tmate.get_fingerprints, return_value=fingerprints),
    )
