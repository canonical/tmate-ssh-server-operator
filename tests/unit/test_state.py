# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm state unit tests."""

from unittest.mock import MagicMock

import ops
import pytest

import state
from state import State


def test_proxyconfig_invalid(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched os.environ mapping that contains invalid proxy values.
    act: when charm state is initialized.
    assert: CharmConfigInvalidError is raised.
    """
    monkeypatch.setattr(state.os, "environ", {"JUJU_CHARM_HTTP_PROXY": "INVALID_URL"})
    mock_charm = MagicMock(spec=ops.CharmBase)
    mock_charm.config = {}

    with pytest.raises(state.CharmConfigInvalidError):
        state.State.from_charm(mock_charm)


def test_invalid_bind_address():
    """
    arrange: given mocked juju network.bind_address.
    act: when the state is initialized.
    assert: InvalidCharmStateError is raised.
    """
    mock_binding = MagicMock(spec=ops.Binding)
    mock_binding.network.bind_address = "invalid_address"
    mock_charm = MagicMock(spec=ops.CharmBase)
    mock_charm.model.get_binding.return_value = mock_binding

    with pytest.raises(state.InvalidCharmStateError):
        State.from_charm(mock_charm)


def test_bind_address_not_ready():
    """
    arrange: given mocked juju model get_binding that isn't ready.
    act: when the state is initialized.
    assert: ip_addr is None.
    """
    mock_charm = MagicMock(spec=ops.CharmBase)
    mock_charm.model.get_binding.return_value = None

    assert not State.from_charm(mock_charm).ip_addr
