# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""tmate-ssh-server charm tmate module unit tests."""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from charms.operator_libs_linux.v0 import apt

import tmate


@pytest.mark.parametrize(
    "exception",
    [
        pytest.param(apt.PackageNotFoundError, id="package not found"),
        pytest.param(apt.PackageError, id="package error"),
    ],
)
def test_install_dependencies_error(exception: type[Exception], monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched apt module that raises an exception.
    act: when install_dependencies is called.
    assert: DependencyInstallError is raised.
    """
    monkeypatch.setattr(tmate.apt, "update", MagicMock(spec=apt.update))
    monkeypatch.setattr(
        tmate.apt, "add_package", MagicMock(spec=apt.add_package, side_effect=[exception])
    )

    with pytest.raises(tmate.DependencyInstallError):
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


def test_start_daemon_error(monkeypatch: pytest.MonkeyPatch):
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
        tmate.subprocess,
        "check_call",
        MagicMock(
            spec=tmate.subprocess.check_call,
            side_effect=[
                None,
                None,
                tmate.subprocess.CalledProcessError(returncode=1, cmd="test"),
            ],
        ),
    )

    with pytest.raises(tmate.DaemonStartError):
        tmate.start_daemon()


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


def test_get_fingerprints_key_install_error(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess.check_output call that raises an error.
    act: when get_fingerprints is called.
    assert: KeyInstallError is raised.
    """
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "RSA_PUB_KEY_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "ED25519_PUB_KEY_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(
        tmate.subprocess,
        "check_output",
        MagicMock(
            spec=tmate.subprocess.check_output,
            side_effect=[
                b"test output",
                tmate.subprocess.CalledProcessError(returncode=1, cmd="test"),
            ],
        ),
    )

    with pytest.raises(tmate.KeyInstallError):
        tmate.get_fingerprints()


def test_get_fingerprints_key_install(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched subprocess.check_output calls.
    act: when get_fingerprints is called.
    assert: Correct fingerprint data is returned.
    """
    monkeypatch.setattr(tmate, "KEYS_DIR", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "RSA_PUB_KEY_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(tmate, "ED25519_PUB_KEY_PATH", MagicMock(spec=Path))
    monkeypatch.setattr(
        tmate.subprocess,
        "check_output",
        MagicMock(
            spec=tmate.subprocess.check_output,
            side_effect=[
                bytes(f"output {(rsa_fingerprint := 'rsa_fingerprint')}", encoding="utf-8"),
                bytes(
                    f"output {(ed25519_fingerprint := 'ed25519_fingerprint')}", encoding="utf-8"
                ),
            ],
        ),
    )

    assert (
        tmate.FingerPrints(rsa=rsa_fingerprint, ed25519=ed25519_fingerprint)
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

    with pytest.raises(tmate.FingerPrintError):
        tmate.generate_tmate_conf(MagicMock())


def test_generate_tmate_conf(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched get_fingerprints that returns mock fingerprint data.
    act: when generate_tmate_conf is called.
    assert: a tmate.conf file contents are generated.
    """
    monkeypatch.setattr(
        tmate,
        "get_fingerprints",
        MagicMock(
            spec=tmate.get_fingerprints,
            return_value=tmate.FingerPrints(
                rsa=(rsa_fingerprint := "rsa_fingerprint"),
                ed25519=(ed25519_fingerprint := "ed25519_fingerprint"),
            ),
        ),
    )
    host = "test_host_value"

    assert (
        textwrap.dedent(
            f"""
        set -g tmate-server-host {host}
        set -g tmate-server-port {tmate.PORT}
        set -g tmate-server-rsa-fingerprint {rsa_fingerprint}
        set -g tmate-server-ed25519-fingerprint {ed25519_fingerprint}
        """
        )
        == tmate.generate_tmate_conf(host)
    )
