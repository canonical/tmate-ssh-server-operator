# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Configurations and functions to operate tmate-ssh-server."""

import base64
import dataclasses
import hashlib
import ipaddress
import logging
import re
import secrets
import string

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
# Published manually and kept equal to the rock version; see CONTRIBUTING.md.
IMAGE_REPOSITORY = "ghcr.io/canonical/tmate-ssh-server"
IMAGE = f"{IMAGE_REPOSITORY}:1.1"

USER = "ubuntu"
GROUP = "ubuntu"

PORT = 10022

# systemd exit codes: https://refspecs.linuxbase.org/LSB_3.0.0/LSB-PDA/LSB-PDA/iniscrptact.html
SYSTEMD_UNIT_NOT_RUNNING_CODE = 3

logger = logging.getLogger(__name__)


class DependencySetupError(Exception):
    """Represents an error while installing and setting up dependencies."""


class KeyInstallError(Exception):
    """Represents an error while installing/generating key files."""


class DaemonError(Exception):
    """Represents an error with the tmate-ssh-server daemon."""


class IncompleteInitError(Exception):
    """The tmate-ssh-server has not been fully initialized."""


class FingerprintError(Exception):
    """Represents an error with generating fingerprints from public keys."""


class DockerError(Exception):
    """Represents an error using a docker command."""


@dataclasses.dataclass
class DaemonStatus:
    """The status of the tmate-ssh-server daemon.

    Attributes:
        running: True if the daemon is running, False otherwise.
        status: The status string of the daemon process.
    """

    running: bool
    status: str


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
            return
        now = datetime.now()
        sleep(check_interval)
    if func():
        return
    raise TimeoutError()


def check_docker_container(name: str) -> bool:
    """Return True if the container is running.

    Args:
        name: The name of the docker container to check.

    Returns:
        True if the container is running, False otherwise.

    Raises:
        DaemonError: If the subprocess command exits with a non-zero exit code.
    """
    try:
        cmd = ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Status}}"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)  # nosec B603
        return "Up" in result.stdout
    except subprocess.CalledProcessError as exc:
        raise DaemonError(
            f"Command {cmd} failed with return code {exc.returncode}. Output: {exc.stdout}"
        ) from exc


def status() -> DaemonStatus:
    """Check the status of the tmate-ssh-server service.

    Returns:
        The status of the tmate-ssh-server daemon.

    Raises:
        DaemonError: if there was an error checking the status of tmate-ssh-server.
    """
    try:
        # Input to subprocess.check_output is trusted, as it is not user input.
        status_str = subprocess.check_output(["systemctl", "status", TMATE_SERVICE_NAME])  # nosec
    except subprocess.CalledProcessError as exc:
        if exc.returncode == SYSTEMD_UNIT_NOT_RUNNING_CODE:
            return DaemonStatus(running=False, status=exc.stdout.decode("utf-8"))
        raise DaemonError("Failed to check tmate-ssh-server status.") from exc

    return DaemonStatus(running=True, status=status_str.decode("utf-8"))


def ensure_daemon_running(address: str) -> None:
    """Run the tmate-ssh-server workload from the charm's current service unit.

    A running workload whose unit is unchanged is kept. Otherwise the unit is installed and the
    workload is (re)started, replacing every container running a tmate-ssh-server image.

    Args:
        address: The IP address to bind to.

    Raises:
        DaemonError: if there was an error starting the tmate-ssh-server docker process.
    """
    installed_content = (
        TMATE_SSH_SERVER_SERVICE_PATH.read_text(encoding="utf-8")
        if TMATE_SSH_SERVER_SERVICE_PATH.exists()
        else None
    )
    name_match = re.search(r"--name (\S+)", installed_content) if installed_content else None
    previous_container = name_match.group(1) if name_match else None
    # Reusing the installed container name makes an unchanged unit render identically.
    container_name = previous_container or "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10)
    )
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"), autoescape=True)
    service_content = environment.get_template("tmate-ssh-server.service.j2").render(
        NAME=container_name,
        WORKDIR=WORK_DIR,
        KEYS_DIR=KEYS_DIR,
        PORT=PORT,
        ADDRESS=address,
        IMAGE=IMAGE,
    )
    # A crash or a failed earlier restart can leave an unchanged unit without a workload.
    if (
        service_content == installed_content
        and check_docker_container(container_name)
        and systemd.service_running(TMATE_SERVICE_NAME)
    ):
        logger.info("tmate-ssh-server unit unchanged, keeping the running workload.")
        return
    _pull_image_and_remove_containers()
    TMATE_SSH_SERVER_SERVICE_PATH.write_text(service_content, encoding="utf-8")
    try:
        systemd.daemon_reload()
        systemd.service_enable(TMATE_SERVICE_NAME)
        systemd.service_restart(TMATE_SERVICE_NAME)
        _wait_for(partial(check_docker_container, container_name), timeout=60)
        _wait_for(partial(systemd.service_running, TMATE_SERVICE_NAME), timeout=60 * 10)
    except systemd.SystemdError as exc:
        raise DaemonError("Failed to start tmate-ssh-server daemon.") from exc
    except TimeoutError as exc:
        raise DaemonError("Timed out waiting for tmate service to start.") from exc


def _pull_image_and_remove_containers() -> None:
    """Pull IMAGE unless it is cached, then force-remove all tmate-ssh-server containers.

    Raises:
        DaemonError: if the image could not be pulled or the containers could not be listed or
            removed.
    """
    # Fetch the image while the old workload still serves, so a registry failure aborts the
    # upgrade instead of leaving the unit without a workload. A cached image is reused, so
    # recovering a crashed workload does not depend on the registry.
    cached = subprocess.run(  # nosec
        ["docker", "image", "inspect", IMAGE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if cached.returncode != 0:
        try:
            subprocess.check_call(["docker", "pull", IMAGE])  # nosec
        except subprocess.CalledProcessError as exc:
            raise DaemonError(f"Failed to pull {IMAGE}.") from exc
    # tmate ignores SIGTERM as the container's PID 1, so stopping the service only kills the
    # docker client and leaves the old container holding the port. Containers the charm does
    # not track, such as ones started by hand, hold the port the same way.
    image_pattern = re.compile(rf"{re.escape(IMAGE_REPOSITORY)}([:@]\S*)?")
    try:
        listing = subprocess.check_output(  # nosec
            ["docker", "ps", "--all", "--format", "{{.ID}} {{.Image}}"], text=True
        )
    except subprocess.CalledProcessError as exc:
        raise DaemonError("Failed to list tmate-ssh-server containers.") from exc
    container_ids = [
        container_id
        for container_id, image in (line.split(maxsplit=1) for line in listing.splitlines())
        if image_pattern.fullmatch(image)
    ]
    if not container_ids:
        return
    try:
        subprocess.check_call(["docker", "rm", "-f", *container_ids])  # nosec
    except subprocess.CalledProcessError as exc:
        raise DaemonError("Failed to remove the previous tmate-ssh-server containers.") from exc


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

    return textwrap.dedent(f"""
        set -g tmate-server-host {host}
        set -g tmate-server-port {PORT}
        set -g tmate-server-rsa-fingerprint {fingerprints.rsa}
        set -g tmate-server-ed25519-fingerprint {fingerprints.ed25519}
        """)


def remove_stopped_containers() -> None:
    """Remove all stopped containers.

    Raises:
        DockerError: if there was an error removing stopped containers.
    """
    try:
        subprocess.check_call(["docker", "container", "prune", "-f"])  # nosec
    except subprocess.CalledProcessError as exc:
        raise DockerError("Failed to remove stopped containers.") from exc
