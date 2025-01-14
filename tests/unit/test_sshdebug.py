# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm sshdebug module unit tests."""

from unittest.mock import MagicMock

import ops
import pytest
from ops.testing import Harness

import tmate
from charm import TmateSSHServerOperatorCharm
from ssh_debug import DEBUG_SSH_INTEGRATION_NAME

from .factories import StateFactory

# Need access to protected functions for testing
# pylint: disable=protected-access


def test_update_relation_data_no_relations(
    monkeypatch: pytest.MonkeyPatch,
    harness: Harness,
    fingerprints: tmate.Fingerprints,
):
    """
    arrange: given debug_ssh integration.
    act: when update_relation_data is called.
    assert: relation data is correctly updated.
    """
    monkeypatch.setattr(
        tmate,
        "get_fingerprints",
        MagicMock(spec=tmate.get_fingerprints, return_value=fingerprints),
    )
    relation_id = harness.add_relation(DEBUG_SSH_INTEGRATION_NAME, "github_runner")
    harness.add_relation_unit(relation_id, "github_runner/0")
    harness.begin()

    charm: TmateSSHServerOperatorCharm = harness.charm
    charm.sshdebug.update_relation_data("host", fingerprints)

    relation_data = harness.get_relation_data(relation_id, charm.unit)
    assert relation_data == {
        "host": "host",
        "port": str(tmate.PORT),
        "rsa_fingerprint": fingerprints.rsa,
        "ed25519_fingerprint": fingerprints.ed25519,
    }


def test__on_ssh_debug_relation_joined_error(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate.get_fingerprints that raises a IncompleteInitError.
    act: when _on_ssh_debug_relation_joined is called.
    assert: the charm raises an error.
    """
    monkeypatch.setattr(
        tmate,
        "get_fingerprints",
        MagicMock(spec=tmate.get_fingerprints, side_effect=[tmate.IncompleteInitError]),
    )

    mock_event = MagicMock(spec=ops.RelationJoinedEvent)

    with pytest.raises(tmate.IncompleteInitError):
        charm.sshdebug._on_ssh_debug_relation_joined(mock_event)


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
    mock_update_relation_data = MagicMock()
    monkeypatch.setattr(charm.sshdebug, "update_relation_data", mock_update_relation_data)

    mock_event = MagicMock(spec=ops.RelationJoinedEvent)
    charm.sshdebug._on_ssh_debug_relation_joined(mock_event)

    mock_update_relation_data.assert_called_once_with(
        host=mock_state.ip_addr, fingerprints=fingerprints
    )
