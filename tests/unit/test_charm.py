# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm unit tests."""

from unittest.mock import MagicMock

import ops
import pytest

import tmate
from charm import TmateSSHServerOperatorCharm
from state import State

# Need access to protected functions for testing
# pylint: disable=protected-access


def test__on_install_dependencies_error(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given mocked tmate install_dependencies function that raises an exception.
    act: when _on_install is called.
    assert: exceptions are re-raised.
    """
    mock_install_deps = MagicMock(
        spec=tmate.install_dependencies, side_effect=[tmate.DependencySetupError]
    )
    monkeypatch.setattr(tmate, "install_dependencies", mock_install_deps)

    with pytest.raises(tmate.DependencySetupError):
        charm._on_install(MagicMock(spec=ops.InstallEvent))


def test__on_install_keys_error(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given mocked tmate instakk_keys function that raises an exception.
    act: when _on_install is called.
    assert: exceptions are re-raised.
    """
    mock_install_deps = MagicMock(spec=tmate.install_dependencies)
    monkeypatch.setattr(tmate, "install_dependencies", mock_install_deps)
    mock_install_deps = MagicMock(spec=tmate.install_keys, side_effect=[tmate.KeyInstallError])
    monkeypatch.setattr(tmate, "install_keys", mock_install_deps)

    with pytest.raises(tmate.KeyInstallError):
        charm._on_install(MagicMock(spec=ops.InstallEvent))


def test__on_install_daemon_error(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given mocked tmate start_daemon function that raises an exception.
    act: when _on_install is called.
    assert: exceptions are re-raised.
    """
    mock_install_deps = MagicMock(spec=tmate.install_dependencies)
    monkeypatch.setattr(tmate, "install_dependencies", mock_install_deps)
    mock_install_keys = MagicMock(spec=tmate.install_keys)
    monkeypatch.setattr(tmate, "install_keys", mock_install_keys)
    mock_install_deps = MagicMock(spec=tmate.start_daemon, side_effect=[tmate.DaemonStartError])
    monkeypatch.setattr(tmate, "start_daemon", mock_install_deps)

    with pytest.raises(tmate.DaemonStartError):
        charm._on_install(MagicMock(spec=ops.InstallEvent))


def test__on_install_defer(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched state.ip_addr that does not yet have a value.
    act: when _on_install is called.
    assert: the event is deferred.
    """
    mock_install_deps = MagicMock(spec=tmate.install_dependencies)
    monkeypatch.setattr(tmate, "install_dependencies", mock_install_deps)
    mock_state = MagicMock(spec=State)
    mock_state.ip_addr = None
    monkeypatch.setattr(charm, "state", mock_state)

    mock_event = MagicMock(spec=ops.InstallEvent)
    charm._on_install(mock_event)

    mock_event.defer.assert_called_once()


def test__on_install(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate installation function calls.
    act: when _on_install is called.
    assert: the unit is in active status.
    """
    monkeypatch.setattr(tmate, "install_dependencies", MagicMock(spec=tmate.install_dependencies))
    monkeypatch.setattr(tmate, "install_keys", MagicMock(spec=tmate.install_keys))
    monkeypatch.setattr(tmate, "start_daemon", MagicMock(spec=tmate.start_daemon))

    mock_event = MagicMock(spec=ops.InstallEvent)
    charm._on_install(mock_event)

    assert charm.unit.status.name == "active"
