# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm actions unit tests."""

from unittest.mock import MagicMock, patch

import ops
import pytest

import tmate
from charm import TmateSSHServerOperatorCharm

from .factories import StateFactory


def test_on_get_server_config_fail(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched state.ip_addr that does not yet have a value.
    act: when on_get_server_config is called.
    assert: the event is failed.
    """
    mock_state = StateFactory(ip_addr=None)
    monkeypatch.setattr(charm.actions, "state", mock_state)

    mock_event = MagicMock(spec=ops.ActionEvent)
    charm.actions.on_get_server_config(mock_event)

    mock_event.fail.assert_called_once()


def test_on_get_server_config_error(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate.generate_tmate_conf that raises an exception.
    act: when on_get_server_config is called.
    assert: the event is failed.
    """
    monkeypatch.setattr(
        tmate,
        "generate_tmate_conf",
        MagicMock(spec=tmate.generate_tmate_conf, side_effect=[tmate.FingerprintError]),
    )

    mock_event = MagicMock(spec=ops.ActionEvent)
    charm.actions.on_get_server_config(mock_event)

    mock_event.fail.assert_called_once()


def test_on_get_server_config(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate.generate_tmate_conf that returns a tmate config.
    act: when on_get_server_config is called.
    assert: the event returns the tmate configuration values.
    """
    monkeypatch.setattr(
        tmate,
        "generate_tmate_conf",
        MagicMock(spec=tmate.generate_tmate_conf, return_value=(value := "test_config_value")),
    )

    mock_event = MagicMock(spec=ops.ActionEvent)
    charm.actions.on_get_server_config(mock_event)

    mock_event.set_results.assert_called_once_with({"tmate-config": value})


def test_on_get_server_config_emits_authz_admin(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate.generate_tmate_conf and a patched owasp_log.
    act: when on_get_server_config discloses the server configuration.
    assert: an authz_admin security event is emitted, so the disclosure is audited.
    """
    monkeypatch.setattr(
        tmate,
        "generate_tmate_conf",
        MagicMock(spec=tmate.generate_tmate_conf, return_value="test_config_value"),
    )

    with patch("actions.owasp_log") as mock_log:
        charm.actions.on_get_server_config(MagicMock(spec=ops.ActionEvent))

    mock_log.authz_admin.assert_called_once_with(
        userid=charm.unit.name,
        admin_activity="get-server-config",
        description=(
            "tmate server configuration (host and SSH key fingerprints) "
            "disclosed via Juju action"
        ),
    )
