# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for tmate-ssh-server-operator charm unit tests."""

import pytest
from ops.testing import Harness

from charm import TmateSSHServerOperatorCharm


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
