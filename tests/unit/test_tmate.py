# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm tmate module unit tests."""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from charms.operator_libs_linux.v0 import apt

import tmate

# Need access to protected functions for testing
# pylint: disable=protected-access


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


def test_install_dependencies_add_user_to_group_error(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched passwd module that raises an exception.
    act: when install_dependencies is called.
    assert: DependencyInstallError is raised.
    """
    monkeypatch.setattr(tmate.apt, "update", MagicMock(spec=apt.update))
    monkeypatch.setattr(tmate.apt, "add_package", MagicMock(spec=apt.add_package))
    monkeypatch.setattr(tmate.passwd, "add_user_to_group", MagicMock(side_effect=[ValueError]))

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


def test_start_daemon_daemon_reload_error(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess call that raises CalledProcessError.
    act: when start_daemon is called.
    assert: DaemonStartError is raised.
    """
    monkeypatch.setattr(tmate, "WORK_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "CREATE_KEYS_SCRIPT_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "TMATE_SSH_SERVER_SERVICE_PATH", MagicMock(spec=Path))
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

    with pytest.raises(tmate.DaemonStartError):
        tmate.start_daemon(address="test")


def test_start_daemon_service_start_error(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess call that raises CalledProcessError.
    act: when start_daemon is called.
    assert: DaemonStartError is raised.
    """
    monkeypatch.setattr(tmate, "WORK_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "CREATE_KEYS_SCRIPT_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "TMATE_SSH_SERVER_SERVICE_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(
        tmate.systemd, "daemon_reload", MagicMock(spec=tmate.systemd.daemon_reload)
    )
    monkeypatch.setattr(
        tmate.systemd,
        "service_start",
        MagicMock(
            spec=tmate.systemd.service_start,
            side_effect=[
                tmate.systemd.SystemdError,
            ],
        ),
    )

    with pytest.raises(tmate.DaemonStartError):
        tmate.start_daemon(address="test")


def test__calculat_fingerprint():
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
    arrange: given a monkeypatched subprocess.check_output calls.
    act: when get_fingerprints is called.
    assert: Correct fingerprint data is returned.
    """
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "RSA_PUB_KEY_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "ED25519_PUB_KEY_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(
        tmate,
        "_calculate_fingerprint",
        MagicMock(
            spec=tmate._calculate_fingerprint,
            side_effect=[(rsa_fingerprint := "rsa"), (ed25519_fingerprint := "ed25519")],
        ),
    )

    assert (
        tmate.Fingerprints(rsa=rsa_fingerprint, ed25519=ed25519_fingerprint)
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

    assert (
        textwrap.dedent(
            f"""
        set -g tmate-server-host {host}
        set -g tmate-server-port {tmate.PORT}
        set -g tmate-server-rsa-fingerprint {fingerprints.rsa}
        set -g tmate-server-ed25519-fingerprint {fingerprints.ed25519}
        """
        )
        == tmate.generate_tmate_conf(host)
    )
