# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for tmate-ssh-server charm."""
import logging
import secrets
from pathlib import Path

import paramiko
from juju.action import Action
from juju.application import Application
from juju.machine import Machine
from juju.unit import Unit
from pytest_operator.plugin import OpsTest

from tmate import PORT

logger = logging.getLogger(__name__)


async def test_ssh_connection(
    ops_test: OpsTest, tmate_ssh_server: Application, tmate_machine: Machine
):
    """
    arrange: given a related github-runner charm and a tmate-ssh-server charm.
    act: when ssh connection is requested.
    assert: the connection is made successfully.
    """
    unit: Unit = next(iter(tmate_ssh_server.units))
    action: Action = await unit.run_action("get-server-config")
    await action.wait()
    assert (
        action.status == "completed"
    ), f"Get server-config action failed, status: {action.status}"
    config = action.results["tmate-config"]

    temp_config_file_path = Path(f"./{secrets.token_hex(8)}")
    temp_config_file_path.write_text(config, encoding="utf-8")
    (retcode, stdout, stderr) = await ops_test.juju(
        "scp", temp_config_file_path.name, f"{tmate_machine.entity_id}:~/.tmate.conf"
    )
    assert retcode == 0, f"Failed to scp tmate conf file {stdout} {stderr}"
    temp_config_file_path.unlink()

    pub_key_path = Path(Path.home() / ".ssh/id_rsa.pub")
    pub_key_contents = pub_key_path.read_text(encoding="utf-8")
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh",
        tmate_machine.entity_id,
        "--",
        f"echo '{pub_key_contents}' >> ~/.ssh/authorized_keys",
    )
    logger.info("Added pub key to authorized_keys, %s %s %s", retcode, stdout, stderr)

    logger.info("Starting tmate session")
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh",
        tmate_machine.entity_id,
        "--",
        "tmate -a ~/.ssh/authorized_keys -S /tmp/tmate.sock new-session -d",
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
        # this is the path to tmate socket that is used by tmate.
        "/tmp/tmate.sock",  # nosec
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
    client.connect(unit_ip, PORT, token, "", compress=True, allow_agent=False)
    transport = client.get_transport()
    assert transport, "Transport wasn't initialized."
    session = transport.open_session()
    session.get_pty()
    session.invoke_shell()
    stdout = session.recv(10000)
    logger.info("Shell stdout: %s", str(stdout))
    # The send expects bytes type but the docstrings want str type (bytes type doesn't work).
    session.send("q\n")  # type: ignore
    stdout = session.recv(10000)
    logger.info("Shell stdout: %s", str(stdout))
    session.send("echo test > ~/test.txt && cat ~/test.txt\n")  # type: ignore
    stdout = session.recv(10000)
    logger.info("Shell stdout: %s", str(stdout))
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh", tmate_machine.entity_id, "cat ~/test.txt"
    )

    assert retcode == 0, f"Error running ssh command, {stdout}, {stderr}"
    assert "test" in stdout, f"Failed to write with ssh command, {stdout}"
