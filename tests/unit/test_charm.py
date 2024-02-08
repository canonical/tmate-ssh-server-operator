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
    mock_install_deps = MagicMock(spec=tmate.start_daemon, side_effect=[tmate.DaemonError])
    monkeypatch.setattr(tmate, "start_daemon", mock_install_deps)

    with pytest.raises(tmate.DaemonError):
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


def test__on_install_error(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate.get_fingerprints that raises an error.
    act: when _on_install is called.
    assert: the charm raises an error.
    """
    mock_install_deps = MagicMock(spec=tmate.install_dependencies)
    monkeypatch.setattr(tmate, "install_dependencies", mock_install_deps)
    monkeypatch.setattr(tmate, "install_keys", MagicMock())
    monkeypatch.setattr(tmate, "start_daemon", MagicMock())
    monkeypatch.setattr(
        tmate, "get_fingerprints", MagicMock(side_effect=[tmate.IncompleteInitError])
    )

    mock_event = MagicMock(spec=ops.InstallEvent)
    with pytest.raises(tmate.IncompleteInitError):
        charm._on_install(mock_event)


def test__on_install(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate installation function calls.
    act: when _on_install is called.
    assert: the unit is in active status and tmate ssh server port is opened.
    """
    monkeypatch.setattr(tmate, "install_dependencies", MagicMock(spec=tmate.install_dependencies))
    monkeypatch.setattr(tmate, "install_keys", MagicMock(spec=tmate.install_keys))
    monkeypatch.setattr(tmate, "start_daemon", MagicMock(spec=tmate.start_daemon))
    monkeypatch.setattr(tmate, "get_fingerprints", MagicMock(spec=tmate.get_fingerprints))

    mock_event = MagicMock(spec=ops.InstallEvent)
    charm._on_install(mock_event)

    assert ops.Port(protocol="tcp", port=tmate.PORT) in charm.unit.opened_ports()
    assert charm.unit.status.name == "active"


def test__on_update_status_ip_not_assigned(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched state.ip_addr that does not yet have a value.
    act: when _on_update_status is called.
    assert: the charm returns and calls no other functions.
    """
    status_mock = MagicMock(return_value=tmate.DaemonStatus(running=True, status=""))
    start_daemon_mock = MagicMock(spec=tmate.start_daemon)
    remove_stopped_containers_mock = MagicMock(spec=tmate.remove_stopped_containers)
    monkeypatch.setattr(tmate, "status", status_mock)
    monkeypatch.setattr(tmate, "start_daemon", start_daemon_mock)
    monkeypatch.setattr(tmate, "remove_stopped_containers", remove_stopped_containers_mock)

    mock_state = MagicMock(spec=State)
    mock_state.ip_addr = None
    monkeypatch.setattr(charm, "state", mock_state)

    mock_event = MagicMock(spec=ops.UpdateStatusEvent)
    charm._on_update_status(mock_event)

    status_mock.assert_not_called()
    start_daemon_mock.assert_not_called()
    remove_stopped_containers_mock.assert_not_called()


def test__on_update_status_error(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given multiple scenarios.
      1. a monkeypatched tmate.status that raises an error.
      2. a monkeypatched tmate.status that returns False for running and
       start_daemon that raises an error.
    act: when _on_update_status is called.
    assert: the errors are not caught
    """
    # 1. tmate.status raises an error
    status_mock = MagicMock(side_effect=tmate.DaemonError)
    start_daemon_mock = MagicMock(spec=tmate.start_daemon)
    monkeypatch.setattr(tmate, "status", status_mock)
    monkeypatch.setattr(tmate, "start_daemon", start_daemon_mock)

    with pytest.raises(tmate.DaemonError):
        charm._on_update_status(MagicMock(spec=ops.UpdateStatusEvent))

    # 2. tmate.is_running returns False for running and start_daemon raises an error
    status_mock.side_effect = [tmate.DaemonStatus(running=False, status="")]
    start_daemon_mock.side_effect = tmate.DaemonError

    with pytest.raises(tmate.DaemonError):
        charm._on_update_status(MagicMock(spec=ops.UpdateStatusEvent))


def test__on_update_status_remove_stopped_containers_error(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
    caplog: pytest.LogCaptureFixture,
):
    """
    arrange: given a monkeypatched tmate.remove_stopped_containers that raises an exception.
    act: when _on_update_status is called.
    assert: the exception is caught and logged.
    """
    monkeypatch.setattr(
        tmate, "status", MagicMock(return_value=tmate.DaemonStatus(running=False, status=""))
    )
    monkeypatch.setattr(tmate, "start_daemon", MagicMock(spec=tmate.start_daemon))
    monkeypatch.setattr(
        tmate, "remove_stopped_containers", MagicMock(side_effect=tmate.DockerError)
    )

    charm._on_update_status(MagicMock(spec=ops.UpdateStatusEvent))

    assert "Failed to remove stopped containers." in caplog.text


def test__on_update_status_restart_daemon(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate.status which returns False for running.
    act: when _on_update_status is called.
    assert: status is set to active, tmate ssh server is restarted and
        stopped docker containers are removed.
    """
    status_mock = MagicMock(return_value=tmate.DaemonStatus(running=False, status=""))
    start_daemon_mock = MagicMock(spec=tmate.start_daemon)
    remove_stopped_containers_mock = MagicMock(spec=tmate.remove_stopped_containers)
    monkeypatch.setattr(tmate, "status", status_mock)
    monkeypatch.setattr(tmate, "start_daemon", start_daemon_mock)
    monkeypatch.setattr(tmate, "remove_stopped_containers", remove_stopped_containers_mock)

    charm._on_update_status(MagicMock(spec=ops.UpdateStatusEvent))

    start_daemon_mock.assert_called_once()
    remove_stopped_containers_mock.assert_called_once()
    assert charm.unit.status.name == "active"


def test__on_update_status_everything_ok(
    monkeypatch: pytest.MonkeyPatch,
    charm: TmateSSHServerOperatorCharm,
):
    """
    arrange: given a monkeypatched tmate.is_running which returns True.
    act: when _on_update_status is called.
    assert: status is set to active, tmate ssh server is not restarted and
        stopped docker containers are not removed.
    """
    status_mock = MagicMock(return_value=tmate.DaemonStatus(running=True, status=""))
    start_daemon_mock = MagicMock(spec=tmate.start_daemon)
    remove_stopped_containers_mock = MagicMock(spec=tmate.remove_stopped_containers)
    monkeypatch.setattr(tmate, "status", status_mock)
    monkeypatch.setattr(tmate, "start_daemon", start_daemon_mock)
    monkeypatch.setattr(tmate, "remove_stopped_containers", remove_stopped_containers_mock)

    charm._on_update_status(MagicMock(spec=ops.UpdateStatusEvent))

    start_daemon_mock.assert_not_called()
    remove_stopped_containers_mock.assert_not_called()
    assert charm.unit.status.name == "active"
