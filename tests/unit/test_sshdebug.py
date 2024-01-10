# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm sshdebug module unit tests."""

from unittest.mock import MagicMock

import ops
import pytest

import tmate
from charm import TmateSSHServerOperatorCharm

from .factories import StateFactory

# Need access to protected functions for testing
# pylint: disable=protected-access


def test__on_ssh_debug_relation_joined_fail(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate.get_fingerprints that raises a KeyInstallError.
    act: when _on_ssh_debug_relation_joined is called.
    assert: the exception is reraised.
    """
    monkeypatch.setattr(
        tmate,
        "get_fingerprints",
        MagicMock(spec=tmate.get_fingerprints, side_effect=[tmate.KeyInstallError]),
    )

    with pytest.raises(tmate.KeyInstallError):
        charm.sshdebug._on_ssh_debug_relation_joined(MagicMock(spec=ops.RelationJoinedEvent))


def test__on_ssh_debug_relation_joined_defer(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate.get_fingerprints that raises a IncompleteInitError.
    act: when _on_ssh_debug_relation_joined is called.
    assert: the event is deferred.
    """
    monkeypatch.setattr(
        tmate,
        "get_fingerprints",
        MagicMock(spec=tmate.get_fingerprints, side_effect=[tmate.IncompleteInitError]),
    )

    mock_event = MagicMock(spec=ops.RelationJoinedEvent)
    charm.sshdebug._on_ssh_debug_relation_joined(mock_event)

    mock_event.defer.assert_called_once()


@pytest.mark.usefixtures("patch_get_fingerprints")
def test__on_ssh_debug_relation_joined(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
    fingerprints: tmate.Fingerprints,
):
    """
    arrange: given a monkeypatched get_fingerprints returning fingerprint data and state.
    act: when _on_ssh_debug_relation_joined is called.
    assert: the relation data is updatedd.
    """
    mock_state = StateFactory()
    monkeypatch.setattr(charm.sshdebug, "state", mock_state)

    mock_event = MagicMock(spec=ops.RelationJoinedEvent)
    mock_event.relation = MagicMock(spec=ops.Relation)
    mock_event.relation.data = MagicMock(spec=ops.RelationData)
    charm.sshdebug._on_ssh_debug_relation_joined(mock_event)

    mock_event.relation.data[charm.model.unit].update.assert_called_once_with(
        {
            "host": mock_state.ip_addr,
            "port": str(tmate.PORT),
            "rsa_fingerprint": fingerprints.rsa,
            "ed25519_fingerprint": fingerprints.ed25519,
        }
    )
