# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Configurations and functions to operate tmate-ssh-server."""

import base64
import dataclasses
import hashlib
import ipaddress
import logging

# subprocess module is required to install and start docker daemon processes, the security
# implications have been considered.
import subprocess  # nosec
import textwrap
import typing
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from time import sleep

import jinja2
from charms.operator_libs_linux.v0 import apt, passwd
from charms.operator_libs_linux.v1 import systemd

import state

APT_DEPENDENCIES = ["openssh-client"]

GIT_REPOSITORY_URL = "https://github.com/tmate-io/tmate-ssh-server.git"

WORK_DIR = Path("/home/ubuntu/")
CREATE_KEYS_SCRIPT_PATH = WORK_DIR / "create_keys.sh"
KEYS_DIR = WORK_DIR / "keys"
RSA_PUB_KEY_PATH = KEYS_DIR / "ssh_host_rsa_key.pub"
ED25519_PUB_KEY_PATH = KEYS_DIR / "ssh_host_ed25519_key.pub"
TMATE_SSH_SERVER_SERVICE_PATH = Path("/etc/systemd/system/tmate-ssh-server.service")
DOCKER_DAEMON_CONFIG_PATH = Path("/etc/docker/daemon.json")
TMATE_SERVICE_NAME = "tmate-ssh-server"

USER = "ubuntu"
GROUP = "ubuntu"

PORT = 10022

logger = logging.getLogger(__name__)


class DependencySetupError(Exception):
    """Represents an error while installing and setting up dependencies."""


class KeyInstallError(Exception):
    """Represents an error while installing/generating key files."""


class DaemonStartError(Exception):
    """Represents an error while starting tmate-ssh-server daemon."""


class IncompleteInitError(Exception):
    """The tmate-ssh-server has not been fully initialized."""


class FingerprintError(Exception):
    """Represents an error with generating fingerprints from public keys."""


def _setup_docker(proxy_config: typing.Optional[state.ProxyConfig] = None) -> None:
    """Install and configure proxy settings for docker if available.

    Args:
        proxy_config: The proxy configuration to enable for dockerd.

    Raises:
        PackageNotFoundError: if the Docker apt package was not found.
        PackageError: if there was a problem installing up Docker apt package.
    """
    if proxy_config:
        environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader("templates"), autoescape=True
        )
        docker_template = environment.get_template("docker_daemon.json.j2")
        daemon_config = docker_template.render(
            HTTP_PROXY=proxy_config.http_proxy,
            HTTPS_PROXY=proxy_config.https_proxy,
            NO_PROXY=proxy_config.no_proxy,
        )
        DOCKER_DAEMON_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        DOCKER_DAEMON_CONFIG_PATH.touch(exist_ok=True)
        DOCKER_DAEMON_CONFIG_PATH.write_text(daemon_config, encoding="utf-8")

    try:
        apt.add_package("docker.io", update_cache=True)
    except (apt.PackageNotFoundError, apt.PackageError) as exc:
        logger.error("Failed to add docker package, %s.", exc)
        raise
    passwd.add_group("docker")
    passwd.add_user_to_group(USER, "docker")


def install_dependencies(proxy_config: typing.Optional[state.ProxyConfig] = None) -> None:
    """Install dependenciese required to start tmate-ssh-server container.

    Args:
        proxy_config: The proxy configuration to enable for dockerd.

    Raises:
        DependencySetupError: if there was something wrong installing the apt package
            dependencies.
    """
    try:
        apt.add_package(APT_DEPENDENCIES, update_cache=True)
        _setup_docker(proxy_config=proxy_config)
    except (apt.PackageNotFoundError, apt.PackageError) as exc:
        raise DependencySetupError("Failed to install apt packages.") from exc


def install_keys(host_ip: typing.Union[ipaddress.IPv4Address, ipaddress.IPv6Address, str]) -> None:
    """Install key creation script and generate keys.

    Args:
        host_ip: The charm host's public IP address.

    Raises:
        KeyInstallError: if there was an error creating ssh keys.
    """
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"), autoescape=True)
    template = environment.get_template("create_keys.sh.j2")
    script = template.render(keys_dir=KEYS_DIR, host=str(host_ip), port=PORT)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    CREATE_KEYS_SCRIPT_PATH.write_text(script, encoding="utf-8")
    try:
        # B603:subprocess_without_shell_equals_true false positive
        # see https://github.com/PyCQA/bandit/issues/333
        subprocess.check_call(["/usr/bin/chown", "-R", f"{USER}:{GROUP}", str(WORK_DIR)])  # nosec
        CREATE_KEYS_SCRIPT_PATH.chmod(755)
        subprocess.check_call([str(CREATE_KEYS_SCRIPT_PATH)])  # nosec
    except subprocess.CalledProcessError as exc:
        raise KeyInstallError from exc


def _wait_for(
    func: typing.Callable[[], typing.Any], timeout: int = 300, check_interval: int = 10
) -> None:
    """Wait for function execution to become truthy.

    Args:
        func: A callback function to wait to return a truthy value.
        timeout: Time in seconds to wait for function result to become truthy.
        check_interval: Time in seconds to wait between ready checks.

    Raises:
        TimeoutError: if the callback function did not return a truthy value within timeout.
    """
    start_time = now = datetime.now()
    min_wait_seconds = timedelta(seconds=timeout)
    while now - start_time < min_wait_seconds:
        if func():
            break
        now = datetime.now()
        sleep(check_interval)
    else:
        if func():
            return
        raise TimeoutError()


def start_daemon(address: str) -> None:
    """Install unit files and start daemon.

    Args:
        address: The IP address to bind to.

    Raises:
        DaemonStartError: if there was an error starting the tmate-ssh-server docker process.
    """
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"), autoescape=True)
    service_content = environment.get_template("tmate-ssh-server.service.j2").render(
        WORKDIR=WORK_DIR,
        KEYS_DIR=KEYS_DIR,
        PORT=PORT,
        ADDRESS=address,
    )
    TMATE_SSH_SERVER_SERVICE_PATH.write_text(service_content, encoding="utf-8")
    try:
        systemd.daemon_reload()
        systemd.service_start(TMATE_SERVICE_NAME)
        _wait_for(partial(systemd.service_running, TMATE_SERVICE_NAME), timeout=60 * 10)
    except systemd.SystemdError as exc:
        raise DaemonStartError("Failed to start tmate-ssh-server daemon.") from exc
    except TimeoutError as exc:
        raise DaemonStartError("Timed out waiting for tmate service to start.") from exc


@dataclasses.dataclass
class Fingerprints:
    """The public key fingerprints.

    Attributes:
        rsa: The RSA public key fingerprint.
        ed25519: The ed25519 public key fingerprint.
    """

    rsa: str
    ed25519: str


def _calculate_fingerprint(key: str) -> str:
    """Calculate the SHA256 fingerprint of a key.

    Args:
        key: Base64 encoded key value.

    Returns:
        Fingerprint of a key.
    """
    decoded_bytes = base64.b64decode(key)
    key_hash = hashlib.sha256(decoded_bytes).digest()
    return base64.b64encode(key_hash).decode("utf-8").removesuffix("=")


def get_fingerprints() -> Fingerprints:
    """Get fingerprint from generated keys.

    Raises:
        IncompleteInitError: if the keys have not been generated by the create_keys.sh script.

    Returns:
        The generated public key fingerprints.
    """
    if not KEYS_DIR.exists() or not RSA_PUB_KEY_PATH.exists() or not ED25519_PUB_KEY_PATH.exists():
        raise IncompleteInitError("Missing keys path(s).")

    # format of a public key is: ssh-rsa <b64-encoded-key> <user>
    rsa_pub_key = RSA_PUB_KEY_PATH.read_text(encoding="utf-8")
    rsa_key_b64 = rsa_pub_key.split()[1]
    rsa_fingerprint = _calculate_fingerprint(rsa_key_b64)

    ed25519_pub_key = ED25519_PUB_KEY_PATH.read_text(encoding="utf-8")
    ed25519_key_b64 = ed25519_pub_key.split()[1]
    ed25519_fingerprint = _calculate_fingerprint(ed25519_key_b64)

    return Fingerprints(rsa=f"SHA256:{rsa_fingerprint}", ed25519=f"SHA256:{ed25519_fingerprint}")


def generate_tmate_conf(host: str) -> str:
    """Generate the .tmate.conf values from generated keys.

    Args:
        host: The host IP address.

    Raises:
        FingerprintError: if there was an error generating fingerprints from public keys.

    Returns:
        The tmate config file contents.
    """
    try:
        fingerprints = get_fingerprints()
    except (IncompleteInitError, KeyInstallError) as exc:
        raise FingerprintError("Error generating fingerprints.") from exc

    return textwrap.dedent(
        f"""
        set -g tmate-server-host {host}
        set -g tmate-server-port {PORT}
        set -g tmate-server-rsa-fingerprint {fingerprints.rsa}
        set -g tmate-server-ed25519-fingerprint {fingerprints.ed25519}
        """
    )
