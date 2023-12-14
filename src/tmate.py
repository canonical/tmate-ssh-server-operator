#!/usr/bin/env python3

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Configurations and functions to operate tmate-ssh-server."""

import ipaddress
import subprocess
import typing
from pathlib import Path

import jinja2
from charms.operator_libs_linux.v0 import apt

APT_DEPENDENCIES = [
    "git-core",
    "build-essential",
    "pkg-config",
    "libtool",
    "libevent-dev",
    "libncurses-dev",
    "zlib1g-dev",
    "automake",
    "libssh-dev",
    "cmake",
    "ruby",
    "libmsgpack-dev",
]

GIT_REPOSITORY_URL = "https://github.com/tmate-io/tmate-ssh-server.git"

WORK_DIR = Path("/home/ubuntu/")
CREATE_KEYS_SCRIPT_PATH = WORK_DIR / "create_keys.sh"
KEYS_DIR = WORK_DIR / "keys"
TMATE_SSH_SERVER_SERVICE_PATH = Path("/etc/systemd/system/tmate-ssh-server.service")

PORT = 10022


class DependencyInstallError(Exception):
    """Represents an error while installing dependencies."""


class KeyInstallError(Exception):
    """Represents an error while installing/generating key files."""


class DaemonStartError(Exception):
    """Represents an error while starting tmate-ssh-server daemon."""


def install_dependencies():
    """Install dependenciese required to start tmate-ssh-server container."""
    try:
        apt.update()
        apt.add_package(["docker.io", "openssh-client"])
    except (apt.PackageNotFoundError, apt.PackageError) as exc:
        raise DependencyInstallError from exc


def install_keys(host_ip: typing.Union[ipaddress.IPv4Address, ipaddress.IPv6Address, str]):
    """Install key creation script and generate keys.

    Args:
        host_ip: The charm host's public IP address.
    """
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"), autoescape=True)
    template = environment.get_template("create_keys.sh.j2")
    script = template.render(keys_dir=KEYS_DIR, host=str(host_ip), port=PORT)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    CREATE_KEYS_SCRIPT_PATH.write_text(script, encoding="utf-8")
    try:
        subprocess.run(["/usr/bin/chown", "-R", "ubuntu:ubuntu", str(WORK_DIR)])
        CREATE_KEYS_SCRIPT_PATH.chmod(755)
        subprocess.check_call(["/usr/bin/sudo", str(CREATE_KEYS_SCRIPT_PATH)])
    except subprocess.CalledProcessError as exc:
        raise KeyInstallError from exc


def start_daemon():
    """Install unit files and start daemon."""
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"), autoescape=True)
    service_content = environment.get_template("tmate-ssh-server.service.j2").render(
        WORKDIR=WORK_DIR,
        KEYS_DIR=KEYS_DIR,
        PORT=PORT,
    )
    TMATE_SSH_SERVER_SERVICE_PATH.write_text(service_content, encoding="utf-8")
    try:
        subprocess.check_call(["/usr/bin/systemctl", "daemon-reload"])
        subprocess.check_call(["/usr/bin/systemctl", "restart", "tmate-ssh-server"])
        subprocess.check_call(["/usr/bin/systemctl", "enable", "tmate-ssh-server"])
    except subprocess.CalledProcessError as exc:
        raise DaemonStartError from exc
