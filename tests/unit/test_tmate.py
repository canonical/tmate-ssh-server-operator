# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm tmate module unit tests."""

# subprocess is used by tmate module. Security implications have been considered.
import re
import subprocess  # nosec
import textwrap
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, call

import pytest
from charms.operator_libs_linux.v0 import apt

import tmate

from .factories import ProxyConfigFactory

# Need access to protected functions for testing
# pylint: disable=protected-access


def test_install_dependencies_proxy_config(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given proxy config, mocked DOCKER_DAEMON_CONFIG_PATH and mocked apt module functions.
    act: when install_dependencies is called.
    assert: docker daemon configuration is written.
    """
    monkeypatch.setattr(tmate.apt, "update", MagicMock(spec=apt.update))
    monkeypatch.setattr(tmate.apt, "add_package", MagicMock(spec=apt.add_package))
    monkeypatch.setattr(tmate.passwd, "add_group", MagicMock(spec=tmate.passwd.add_group))
    monkeypatch.setattr(
        tmate.passwd, "add_user_to_group", MagicMock(spec=tmate.passwd.add_user_to_group)
    )
    proxy_config = ProxyConfigFactory()

    with NamedTemporaryFile() as temporary_docker_daemon_file:
        monkeypatch.setattr(
            tmate,
            "DOCKER_DAEMON_CONFIG_PATH",
            (tmp_file_path := Path(temporary_docker_daemon_file.name)),
        )
        # ProxyConfigFactory is not considered as ProxyConfig for mypy
        tmate.install_dependencies(proxy_config=proxy_config)  # type: ignore

        assert f"""{{
  "proxies": {{
    "http-proxy": "{proxy_config.http_proxy}",
    "https-proxy": "{proxy_config.https_proxy}",
    "no-proxy": "{proxy_config.no_proxy}"
  }}
}}""" == tmp_file_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "exception",
    [
        pytest.param(apt.PackageNotFoundError, id="package not found"),
        pytest.param(apt.PackageError, id="package error"),
    ],
)
def test__setup_docker_error(exception: type[Exception], monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched apt module that raises an exception.
    act: when _setup_docker is called.
    assert: DependencyInstallError is raised.
    """
    monkeypatch.setattr(tmate.apt, "update", MagicMock(spec=apt.update))
    monkeypatch.setattr(
        tmate.apt, "add_package", MagicMock(spec=apt.add_package, side_effect=[exception])
    )

    with pytest.raises(exception):
        tmate._setup_docker()


@pytest.mark.parametrize(
    "exception",
    [
        pytest.param(apt.PackageNotFoundError, id="package not found"),
        pytest.param(apt.PackageError, id="package error"),
    ],
)
def test_install_dependencies_apt_error(
    exception: type[Exception], monkeypatch: pytest.MonkeyPatch
):
    """
    arrange: given a monkeypatched apt module that raises an exception.
    act: when install_dependencies is called.
    assert: DependencyInstallError is raised.
    """
    monkeypatch.setattr(tmate.apt, "update", MagicMock(spec=apt.update))
    monkeypatch.setattr(
        tmate.apt, "add_package", MagicMock(spec=apt.add_package, side_effect=[exception])
    )

    with pytest.raises(tmate.DependencySetupError):
        tmate.install_dependencies()


def test_install_keys_error(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess call that raises CalledProcessError.
    act: when install_keys is called.
    assert: KeyInstallError is raised.
    """
    monkeypatch.setattr(tmate, "WORK_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "CREATE_KEYS_SCRIPT_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(
        tmate.subprocess,
        "check_call",
        MagicMock(
            spec=tmate.subprocess.check_call,
            side_effect=[tmate.subprocess.CalledProcessError(returncode=1, cmd="test")],
        ),
    )

    with pytest.raises(tmate.KeyInstallError):
        tmate.install_keys(MagicMock())


def test_install_keys(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess call.
    act: when install_keys is called.
    assert: KeyInstallError is raised.
    """
    monkeypatch.setattr(tmate, "WORK_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "CREATE_KEYS_SCRIPT_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(
        tmate.subprocess,
        "check_call",
        MagicMock(spec=tmate.subprocess.check_call),
    )

    tmate.install_keys(MagicMock())


def test__wait_for_timeout_error(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a mock function that returns Falsy value.
    act: when _wait_for function is called.
    assert: TimeoutError is raised.
    """
    monkeypatch.setattr(tmate, "sleep", MagicMock(spec=tmate.sleep))  # to speed up testing
    mock_func = MagicMock(return_value=False)

    with pytest.raises(TimeoutError):
        tmate._wait_for(mock_func, timeout=2, check_interval=1)


@pytest.mark.parametrize(
    "timeout, interval",
    [
        pytest.param(
            3,
            1,
            id="within interval",
        ),
        pytest.param(0, 1, id="last check"),
    ],
)
def test__wait_for(monkeypatch: pytest.MonkeyPatch, timeout: int, interval: int):
    """
    arrange: given a mock function that returns Truthy value.
    act: when _wait_for function is called.
    assert: the function returns without raising an error.
    """
    monkeypatch.setattr(tmate, "sleep", MagicMock(spec=tmate.sleep))  # to speed up testing
    mock_func = MagicMock(return_value=True)

    tmate._wait_for(mock_func, timeout=timeout, check_interval=interval)


def test_status(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess call which returns zero exit code.
    act: when is_running is called.
    assert: the output of the systemd call is returned.
    """
    subprocess_mock = MagicMock(spec=tmate.subprocess.check_output, return_value=b"active")
    monkeypatch.setattr(tmate.subprocess, "check_output", subprocess_mock)

    assert tmate.status() == tmate.DaemonStatus(running=True, status="active")


def test_status_not_running(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess call which returns unit not running exit code.
    act: when is_running is called.
    assert: the output of the systemd call is returned.
    """
    subprocess_mock = MagicMock(
        spec=tmate.subprocess.check_output,
        side_effect=subprocess.CalledProcessError(
            tmate.SYSTEMD_UNIT_NOT_RUNNING_CODE, "test", output=b"inactive"
        ),
    )
    monkeypatch.setattr(tmate.subprocess, "check_output", subprocess_mock)

    assert tmate.status() == tmate.DaemonStatus(running=False, status="inactive")


def test_status_error(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess call that raises an error.
        This error does not indicate that the service is not running.
    act: when status is called.
    assert: DaemonError is raised in both cases
    """
    subprocess_mock = MagicMock(
        spec=tmate.subprocess.check_output, side_effect=subprocess.CalledProcessError(1, "test")
    )
    monkeypatch.setattr(tmate.subprocess, "check_output", subprocess_mock)

    with pytest.raises(tmate.DaemonError) as exc:
        tmate.status()
    assert "Failed to check tmate-ssh-server status." in str(exc.value)


def test_ensure_daemon_running_daemon_reload_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """
    arrange: given a monkeypatched systemd call that raises SystemdError.
    act: when ensure_daemon_running is called.
    assert: DaemonError is raised.
    """
    monkeypatch.setattr(tmate, "WORK_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "CREATE_KEYS_SCRIPT_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "TMATE_SSH_SERVER_SERVICE_PATH", tmp_path / "tmate.service")
    monkeypatch.setattr(
        tmate.systemd,
        "daemon_reload",
        MagicMock(
            spec=tmate.systemd.daemon_reload,
            side_effect=[
                tmate.systemd.SystemdError,
            ],
        ),
    )
    with pytest.raises(tmate.DaemonError) as exc:
        tmate.ensure_daemon_running(address="test")

    assert "Failed to start tmate-ssh-server daemon." in str(exc.value)


def test_ensure_daemon_running_systemd_service_timeout_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """
    arrange: given a monkeypatched _wait_for systemd service all that raises a timeout error.
    act: when ensure_daemon_running is called.
    assert: DaemonError is raised.
    """
    monkeypatch.setattr(tmate, "WORK_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "CREATE_KEYS_SCRIPT_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "TMATE_SSH_SERVER_SERVICE_PATH", tmp_path / "tmate.service")
    monkeypatch.setattr(
        tmate.systemd,
        "daemon_reload",
        MagicMock(spec=tmate.systemd.daemon_reload),
    )
    monkeypatch.setattr(
        tmate.systemd,
        "service_enable",
        MagicMock(spec=tmate.systemd.service_enable),
    )
    monkeypatch.setattr(
        tmate.systemd,
        "service_restart",
        MagicMock(spec=tmate.systemd.service_restart),
    )

    def wait_for_side_effect(*args, **kwargs):  # pylint: disable=unused-argument
        """Simulate waiting for a service to start.

        Args:
            args: Positional arguments.
            kwargs: Keyword arguments.

        Raises:
            TimeoutError: On second call to simulate timeout.
        """
        if not hasattr(wait_for_side_effect, "called_once"):
            # defined at runtime
            wait_for_side_effect.called_once = True  # type: ignore[attr-defined]
            return
        raise TimeoutError

    monkeypatch.setattr(
        tmate,
        "_wait_for",
        MagicMock(spec=tmate._wait_for, side_effect=wait_for_side_effect),
    )

    with pytest.raises(tmate.DaemonError) as exc:
        tmate.ensure_daemon_running(address="test")

    assert "Timed out waiting for tmate service to start." in str(exc.value)


def test_ensure_daemon_running_enable_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """
    arrange: given a monkeypatched systemd call that raises SystemdError.
    act: when enable_daemon is called.
    assert: DaemonError is raised.
    """
    monkeypatch.setattr(tmate, "WORK_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "CREATE_KEYS_SCRIPT_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "TMATE_SSH_SERVER_SERVICE_PATH", tmp_path / "tmate.service")
    monkeypatch.setattr(
        tmate.systemd,
        "daemon_reload",
        MagicMock(spec=tmate.systemd.daemon_reload),
    )
    monkeypatch.setattr(
        tmate.systemd,
        "service_enable",
        MagicMock(
            spec=tmate.systemd.service_enable,
            side_effect=[
                tmate.systemd.SystemdError,
            ],
        ),
    )

    with pytest.raises(tmate.DaemonError):
        tmate.ensure_daemon_running(address="test")


def test_ensure_daemon_running_service_restart_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """
    arrange: given a monkeypatched systemd that raises SystemdError.
    act: when ensure_daemon_running is called.
    assert: DaemonError is raised.
    """
    monkeypatch.setattr(tmate, "WORK_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "CREATE_KEYS_SCRIPT_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "TMATE_SSH_SERVER_SERVICE_PATH", tmp_path / "tmate.service")
    monkeypatch.setattr(
        tmate.systemd, "daemon_reload", MagicMock(spec=tmate.systemd.daemon_reload)
    )
    monkeypatch.setattr(
        tmate.systemd,
        "service_enable",
        MagicMock(spec=tmate.systemd.service_enable),
    )
    monkeypatch.setattr(
        tmate.systemd,
        "service_restart",
        MagicMock(
            spec=tmate.systemd.service_restart,
            side_effect=[
                tmate.systemd.SystemdError,
            ],
        ),
    )

    with pytest.raises(tmate.DaemonError):
        tmate.ensure_daemon_running(address="test")


@pytest.mark.parametrize(
    "stdout, result",
    [
        pytest.param("Up 5 minutes", True, id="container running"),
        pytest.param("Exited (0) 2 minutes ago", False, id="container not running"),
    ],
)
def test_check_docker_container(monkeypatch: pytest.MonkeyPatch, stdout, result):
    """
    arrange: given a monkeypatched subprocess call.
    act: when check_docker_container is called.
    assert: The function returns expected value without raising any errors.
    """
    mock_result = MagicMock()
    mock_result.stdout = stdout
    monkeypatch.setattr(tmate.subprocess, "run", MagicMock(return_value=mock_result))

    assert tmate.check_docker_container(name="test") == result


def test_check_docker_container_subprocess_error(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess call that raises CalledProcessError.
    act: when check_docker_container is called.
    assert: DaemonError is raised.
    """
    monkeypatch.setattr(
        tmate.subprocess,
        "run",
        MagicMock(
            spec=tmate.subprocess.run,
            side_effect=[tmate.subprocess.CalledProcessError(returncode=1, cmd="test")],
        ),
    )

    with pytest.raises(tmate.DaemonError):
        tmate.check_docker_container(name="test")


def test__calculate_fingerprint():
    """
    arrange: given a test fingerprint data.
    act: when _calculate_fingerprint is called.
    assert: correct fingerprint data is returned.
    """
    test_b64_pub_key_data = "AAAAB3NzaC1yc2EAAAADAQABAAABgQDt5qyv585y8lKFoirTyexOR9YwMSzihoDG/N6mi\
    FzHv/22Fd/6NN96Xymf8HGoUdR6KhUZ3SQRwUmmPRb2eASaOBvDzDdSSzWT6N2DuW31WXw/Kw1DUXZ6AWyAH5O3Y5kvmD\
    7prT3QGVgOKtm9Cy/EeXzNdbiK6sTbfER2k6KZpjdz/onA0iovd7N2SrxZwSfvhZ6sTpD//WDTmN/bV+W+6/d3zNYwak4\
    mNPRNTC1hcjBryOMYJ2Q0MnjAtWf7MKU1IvNYiWUZlPKVBlPuDxML/4kSf5xbC/qG2EIyYsywHErfThX2sOZuU2gc+4+1\
    mb1YZpEpPDGLN/l4Er2gtQaW8qes6JozuGmjU6+ZZt7sLqYrBSChJbHlDPDNee9mjMRVPXtppqzpmpZsYR7N7PoRC+KLe\
    K/4OQKLtHSYxKVCf4dGaDvgxsoG4AyECE7is3bMlkc87GxhV0IEb1A1iZ3ycAxIrmP9G5g2Nao/OL9G4zVW9AY4Lg4M4k\
    H26zctvb0="

    assert (
        tmate._calculate_fingerprint(test_b64_pub_key_data)
        == "uW23WW14JnjeVLUg4kWvbhWptvjAbODK2d4jJmnQyqI"
    )


def test_get_fingerprints_incomplete_init_error(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched paths that don't exist.
    act: when get_fingerprints is called.
    assert: IncompleteInitError is raised.
    """
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = False
    monkeypatch.setattr(tmate, "KEYS_DIR", mock_path)

    with pytest.raises(tmate.IncompleteInitError):
        tmate.get_fingerprints()


def test_get_fingerprints(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched _calculate_fingerprint method.
    act: when get_fingerprints is called.
    assert: Correct fingerprint data is returned.
    """
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "RSA_PUB_KEY_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "ED25519_PUB_KEY_PATH", MagicMock(spec=Path))
    rsa_fingerprint = "rsa"
    ed25519_fingerprint = "ed25519"
    monkeypatch.setattr(
        tmate,
        "_calculate_fingerprint",
        MagicMock(
            spec=tmate._calculate_fingerprint,
            side_effect=[(rsa_fingerprint), (ed25519_fingerprint)],
        ),
    )

    assert (
        tmate.Fingerprints(
            rsa=f"SHA256:{rsa_fingerprint}", ed25519=f"SHA256:{ed25519_fingerprint}"
        )
        == tmate.get_fingerprints()
    )


@pytest.mark.parametrize(
    "exception",
    [
        pytest.param(tmate.IncompleteInitError, id="incomplete init"),
        pytest.param(tmate.KeyInstallError, id="key install error"),
    ],
)
def test_generate_tmate_conf_error(monkeypatch: pytest.MonkeyPatch, exception: type[Exception]):
    """
    arrange: given a monkeypatched get_fingerprints that raises exceptions.
    act: when generate_tmate_conf is called.
    assert: FingerPrintError is raised.
    """
    monkeypatch.setattr(
        tmate, "get_fingerprints", MagicMock(spec=tmate.get_fingerprints, side_effect=[exception])
    )

    with pytest.raises(tmate.FingerprintError):
        tmate.generate_tmate_conf(MagicMock())


@pytest.mark.usefixtures("patch_get_fingerprints")
def test_generate_tmate_conf(fingerprints: tmate.Fingerprints):
    """
    arrange: given a monkeypatched get_fingerprints that returns mock fingerprint data.
    act: when generate_tmate_conf is called.
    assert: a tmate.conf file contents are generated.
    """
    host = "test_host_value"

    assert textwrap.dedent(f"""
        set -g tmate-server-host {host}
        set -g tmate-server-port {tmate.PORT}
        set -g tmate-server-rsa-fingerprint {fingerprints.rsa}
        set -g tmate-server-ed25519-fingerprint {fingerprints.ed25519}
        """) == tmate.generate_tmate_conf(host)


def test_remove_stopped_containers_error(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess call that raises CalledProcessError.
    act: when remove_stopped_containers is called.
    assert: DockerError is raised.
    """
    monkeypatch.setattr(
        tmate.subprocess,
        "check_call",
        MagicMock(
            spec=tmate.subprocess.check_call,
            side_effect=[tmate.subprocess.CalledProcessError(returncode=1, cmd="test")],
        ),
    )

    with pytest.raises(tmate.DockerError):
        tmate.remove_stopped_containers()


def _mock_workload_calls(monkeypatch: pytest.MonkeyPatch, image_cached: bool) -> MagicMock:
    """Record docker and systemd calls made by ensure_daemon_running on a single mock.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        image_cached: Whether `docker image inspect` finds IMAGE locally.

    Returns:
        The parent mock whose mock_calls hold the ordered calls.
    """
    calls_mock = MagicMock()
    calls_mock.run.return_value.returncode = 0 if image_cached else 1
    monkeypatch.setattr(tmate.subprocess, "run", calls_mock.run)
    monkeypatch.setattr(tmate.subprocess, "check_call", calls_mock.check_call)
    monkeypatch.setattr(tmate.systemd, "daemon_reload", calls_mock.daemon_reload)
    monkeypatch.setattr(tmate.systemd, "service_enable", calls_mock.service_enable)
    monkeypatch.setattr(tmate.systemd, "service_restart", calls_mock.service_restart)
    monkeypatch.setattr(tmate, "_wait_for", MagicMock())
    return calls_mock


@pytest.mark.parametrize(
    "installed_unit, expected_calls",
    [
        pytest.param(
            None, ["daemon_reload", "service_enable", "service_restart"], id="fresh install"
        ),
        pytest.param(
            "ExecStart=docker run --name legacy0001 --user root "
            "ghcr.io/canonical/tmate-ssh-server:0.1.1",
            [
                "run",
                "check_call",
                "check_call",
                "daemon_reload",
                "service_enable",
                "service_restart",
            ],
            id="legacy unit",
        ),
    ],
)
def test_ensure_daemon_running_installs_unit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    installed_unit: str | None,
    expected_calls: list[str],
):
    """
    arrange: given no service unit, or one running a legacy container, and an uncached image.
    act: when the daemon is ensured to be running.
    assert: the patched image is rendered and the service restarted; a legacy container is
        replaced after pulling the image, keeping its name.
    """
    unit_path = tmp_path / "tmate-ssh-server.service"
    if installed_unit is not None:
        unit_path.write_text(installed_unit)
    monkeypatch.setattr(tmate, "TMATE_SSH_SERVER_SERVICE_PATH", unit_path)
    calls_mock = _mock_workload_calls(monkeypatch, image_cached=False)

    tmate.ensure_daemon_running(address="10.0.0.10")

    assert "docker run --rm --name" in unit_path.read_text()
    assert tmate.IMAGE in unit_path.read_text()
    assert ("--name legacy0001 " in unit_path.read_text()) == (installed_unit is not None)
    assert [call[0] for call in calls_mock.mock_calls] == expected_calls
    if installed_unit is not None:
        assert calls_mock.check_call.call_args_list == [
            call(["docker", "pull", tmate.IMAGE]),
            call(["docker", "rm", "-f", "legacy0001"]),
        ]
    calls_mock.service_restart.assert_called_once_with(tmate.TMATE_SERVICE_NAME)


@pytest.mark.parametrize(
    "address, expect_restart",
    [
        pytest.param("10.0.0.10", False, id="unchanged unit"),
        pytest.param("10.0.0.11", True, id="changed address"),
    ],
)
def test_ensure_daemon_running_restarts_only_on_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, address: str, expect_restart: bool
):
    """
    arrange: given a service unit installed by the current charm and a healthy workload.
    act: when the daemon is ensured to be running with the same or a different address.
    assert: the workload is left running when the unit is unchanged, and is replaced otherwise.
    """
    unit_path = tmp_path / "tmate-ssh-server.service"
    monkeypatch.setattr(tmate, "TMATE_SSH_SERVER_SERVICE_PATH", unit_path)
    calls_mock = _mock_workload_calls(monkeypatch, image_cached=False)
    monkeypatch.setattr(tmate, "check_docker_container", MagicMock(return_value=True))
    monkeypatch.setattr(tmate.systemd, "service_running", MagicMock(return_value=True))
    tmate.ensure_daemon_running(address="10.0.0.10")
    installed_unit = unit_path.read_text()
    calls_mock.reset_mock()

    tmate.ensure_daemon_running(address=address)

    if expect_restart:
        assert unit_path.read_text() != installed_unit
        assert [call[0] for call in calls_mock.mock_calls] == [
            "run",
            "check_call",
            "check_call",
            "daemon_reload",
            "service_enable",
            "service_restart",
        ]
    else:
        assert unit_path.read_text() == installed_unit
        assert not calls_mock.mock_calls


@pytest.mark.parametrize(
    "container_running, service_running, image_cached",
    [
        pytest.param(False, True, False, id="container down"),
        pytest.param(True, False, False, id="service down"),
        pytest.param(False, False, True, id="image cached"),
    ],
)
def test_ensure_daemon_running_recovers_unchanged_unit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    container_running: bool,
    service_running: bool,
    image_cached: bool,
):
    """
    arrange: given an unchanged service unit whose workload is down.
    act: when the daemon is ensured to be running.
    assert: the workload is restarted, as needed after a crash or failed upgrade, pulling the
        image only when it is not cached.
    """
    unit_path = tmp_path / "tmate-ssh-server.service"
    monkeypatch.setattr(tmate, "TMATE_SSH_SERVER_SERVICE_PATH", unit_path)
    calls_mock = _mock_workload_calls(monkeypatch, image_cached=image_cached)
    tmate.ensure_daemon_running(address="10.0.0.10")
    installed_unit = unit_path.read_text()
    calls_mock.reset_mock()
    monkeypatch.setattr(tmate, "check_docker_container", MagicMock(return_value=container_running))
    monkeypatch.setattr(tmate.systemd, "service_running", MagicMock(return_value=service_running))

    tmate.ensure_daemon_running(address="10.0.0.10")

    assert unit_path.read_text() == installed_unit
    pull_calls = [] if image_cached else ["check_call"]
    assert [call[0] for call in calls_mock.mock_calls] == [
        "run",
        *pull_calls,
        "check_call",
        "daemon_reload",
        "service_enable",
        "service_restart",
    ]
    name_match = re.search(r"--name (\S+)", installed_unit)
    assert name_match
    assert calls_mock.check_call.call_args_list[-1] == call(
        ["docker", "rm", "-f", name_match.group(1)]
    )


@pytest.mark.parametrize(
    "check_call_effects, service_restart_error, match",
    [
        pytest.param(
            [tmate.subprocess.CalledProcessError(returncode=1, cmd="docker")],
            None,
            "Failed to pull",
            id="image pull fails",
        ),
        pytest.param(
            [None, tmate.subprocess.CalledProcessError(returncode=1, cmd="docker")],
            None,
            "Failed to remove",
            id="container removal fails",
        ),
        pytest.param(
            [None, None], tmate.systemd.SystemdError, "Failed to start", id="restart fails"
        ),
    ],
)
def test_ensure_daemon_running_replace_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    check_call_effects: list[Exception | None],
    service_restart_error: type[Exception] | None,
    match: str,
):
    """
    arrange: given a legacy unit, an uncached image and a failing replacement step.
    act: when the daemon is ensured to be running.
    assert: the failure is translated to a workload error, and a failure before the old
        container is removed leaves its unit untouched.
    """
    unit_path = tmp_path / "tmate.service"
    unit_path.write_text("ExecStart=docker run --name legacy0001 image")
    monkeypatch.setattr(tmate, "TMATE_SSH_SERVER_SERVICE_PATH", unit_path)
    monkeypatch.setattr(tmate.subprocess, "run", MagicMock(return_value=MagicMock(returncode=1)))
    check_call_mock = MagicMock(side_effect=check_call_effects)
    monkeypatch.setattr(tmate.subprocess, "check_call", check_call_mock)
    monkeypatch.setattr(tmate.systemd, "daemon_reload", MagicMock())
    monkeypatch.setattr(tmate.systemd, "service_enable", MagicMock())
    monkeypatch.setattr(
        tmate.systemd, "service_restart", MagicMock(side_effect=service_restart_error)
    )

    with pytest.raises(tmate.DaemonError, match=match):
        tmate.ensure_daemon_running(address="10.0.0.10")

    assert check_call_mock.call_count == len(check_call_effects)
    if check_call_effects[-1] is not None:
        assert unit_path.read_text() == "ExecStart=docker run --name legacy0001 image"
