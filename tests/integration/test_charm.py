# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for tmate-ssh-server charm."""
import asyncio
import logging
import os
import secrets

# library stubs for paramiko are in a separate python package and does not need to be installed.
import paramiko  # type: ignore
from juju.action import Action
from juju.application import Application
from juju.machine import Machine
from juju.unit import Unit
from pytest_operator.plugin import OpsTest

from tmate import PORT

from .helpers import wait_for

logger = logging.getLogger(__name__)


async def test_ssh_connection(
    # ops_test: OpsTest, tmate_ssh_server: Application, tmate_machine: Machine
):
    """
    arrange: given a related github-runner charm and a tmate-ssh-server charm.
    act: when ssh connection is requested.
    assert: the connection is made successfully.
    """
    assert False, "Testing"
    unit: Unit = next(iter(tmate_ssh_server.units))
    action: Action = await unit.run_action("get-server-config")
    await action.wait()
    config = action.results["tmate-config"]

    with open(secrets.token_hex(8), mode="x", encoding="utf-8") as config_file:
        config_file.write(config)
    (retcode, stdout, stderr) = await ops_test.juju(
        "scp", config_file.name, f"{tmate_machine.entity_id}:~/.tmate.conf"
    )
    assert retcode == 0, f"Failed to scp tmate conf file {stdout} {stderr}"
    os.remove(config_file.name)

    logger.info("Starting tmate session")
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh", tmate_machine.entity_id, "--", "tmate -S /tmp/tmate.sock new-session -d"
    )
    assert retcode == 0, f"Error running ssh display command, {stdout}, {stderr}"
    logger.info("New session created %s %s %s", retcode, stdout, stderr)
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh", tmate_machine.entity_id, "--", "tmate -S /tmp/tmate.sock wait tmate-ready"
    )
    assert retcode == 0, f"Error running ssh display command, {stdout}, {stderr}"
    logger.info("Tmate ready %s %s %s", retcode, stdout, stderr)
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh",
        tmate_machine.entity_id,
        "--",
        "tmate",
        "-S",
        "/tmp/tmate.sock",
        "display",
        "-p",
        "'#{tmate_ssh}'",
    )
    assert retcode == 0, f"Error running ssh display command, {stdout}, {stderr}"
    logger.info("Tmate connection output: %s %s %s", retcode, stdout, stderr)

    token = stdout.split(" ")[2].split("@")[0]
    client = paramiko.SSHClient()
    unit_ip = await unit.get_public_address()
    # trust missing host key for testing purposes only.
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # nosec
    logger.info("Connecting to created ssh session, %s %s %s", unit_ip, PORT, token)
    client.connect(unit_ip, PORT, token, compress=True, allow_agent=False)
    transport = client.get_transport()
    session = transport.open_session()
    session.get_pty()
    session.invoke_shell()
    stdout = session.recv(10000)
    logger.info("Shell stdout: %s", stdout)
    session.send("q\n")
    stdout = session.recv(10000)
    logger.info("Shell stdout: %s", stdout)
    session.send("echo test > ~/test.txt && cat ~/test.txt\n")
    stdout = session.recv(10000)
    logger.info("Shell stdout: %s", stdout)
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh", tmate_machine.entity_id, "cat ~/test.txt"
    )

    assert retcode == 0, f"Error running ssh command, {stdout}, {stderr}"
    assert "test" in stdout, f"Failed to write with ssh command, {stdout}"
