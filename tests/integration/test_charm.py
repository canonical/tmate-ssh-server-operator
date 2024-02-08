# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for tmate-ssh-server charm."""
import logging
import secrets
from pathlib import Path

import paramiko
from juju.application import Application
from juju.machine import Machine
from juju.unit import Unit
from ops import ActiveStatus
from pytest_operator.plugin import OpsTest

from tmate import PORT

SHELL_STDOUT_LOG_STR = "Shell stdout: %s"

logger = logging.getLogger(__name__)


async def test_ssh_connection(
    ops_test: OpsTest, tmate_config: str, unit: Unit, tmate_machine: Machine, pub_key: str
):
    """
    arrange: given a related machine charm and a tmate-ssh-server charm.
    act: when ssh connection is requested.
    assert: the connection is made successfully.
    """
    temp_config_file_path = Path(f"./{secrets.token_hex(8)}")
    temp_config_file_path.write_text(tmate_config, encoding="utf-8")
    (retcode, stdout, stderr) = await ops_test.juju(
        "scp", temp_config_file_path.name, f"{tmate_machine.entity_id}:~/.tmate.conf"
    )
    assert retcode == 0, f"Failed to scp tmate conf file {stdout} {stderr}"
    temp_config_file_path.unlink()

    await ops_test.juju(
        "ssh", tmate_machine.entity_id, "--", f"echo '{pub_key}' >> ~/.ssh/authorized_keys"
    )

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
        "ssh", tmate_machine.entity_id, "--", "tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'"
    )
    assert retcode == 0, f"Error running ssh display command, {stdout}, {stderr}"
    logger.info("Tmate connection output: %s %s %s", retcode, stdout, stderr)

    token = stdout.split(" ")[2].split("@")[0]
    client = paramiko.SSHClient()
    unit_ip = await unit.get_public_address()
    # trust missing host key for testing purposes only.
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # nosec
    logger.info("Connecting to created ssh session, %s %s %s", unit_ip, PORT, token)
    client.connect(
        unit_ip,
        PORT,
        token,
        compress=True,
        allow_agent=False,
        key_filename=f"{Path.home()}/.ssh/id_rsa.pub",
    )
    transport = client.get_transport()
    assert transport, "Transport wasn't initialized."
    session = transport.open_session()
    session.get_pty()
    session.invoke_shell()
    stdout = session.recv(10000)
    logger.info(SHELL_STDOUT_LOG_STR, str(stdout))
    # The send expects bytes type but the docstrings want str type (bytes type doesn't work).
    session.send("q\n")  # type: ignore
    stdout = session.recv(10000)
    logger.info(SHELL_STDOUT_LOG_STR, str(stdout))
    session.send("echo test > ~/test.txt && cat ~/test.txt\n")  # type: ignore
    stdout = session.recv(10000)
    logger.info(SHELL_STDOUT_LOG_STR, str(stdout))
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh", tmate_machine.entity_id, "cat ~/test.txt"
    )

    assert retcode == 0, f"Error running ssh command, {stdout}, {stderr}"
    assert "test" in stdout, f"Failed to write with ssh command, {stdout}"


async def test_restart_of_inactive_service(ops_test: OpsTest, unit: Unit, tmate_ssh_server: Application):
    """
    arrange: given a tmate-ssh-server charm unit.
    act: kill the docker process containing the service and
     fast-forward to next update status event.
    assert: the service has been restarted successfully.
    """
    await ops_test.juju("ssh", unit.entity_id, "--", "docker stop $(docker ps -q)")
    (retcode, stdout, stderr) = await ops_test.juju("ssh", unit.entity_id, "--", "docker ps")
    assert retcode == 0, f"Error running docker ps command, {stdout}, {stderr}"
    assert "tmate-ssh-server" not in stdout, "tmate-ssh-server service is still running"
    (retcode, _, _) = await ops_test.juju(
        "ssh", unit.entity_id, "--", "systemctl status --quiet is-active tmate-ssh-server"
    )
    assert retcode != 0, "tmate-ssh-server service is still running"

    async with ops_test.fast_forward():
        await unit.model.wait_for_idle(apps=[tmate_ssh_server.name], status=ActiveStatus.name)

    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh", unit.entity_id, "--", "systemctl status --quiet is-active tmate-ssh-server"
    )
    assert retcode == 0, f"tmate-ssh-server service is not running, {stdout}, {stderr}"

    (retcode, stdout, stderr) = await ops_test.juju("ssh", unit.entity_id, "--", "docker ps")
    assert retcode == 0, f"Error running docker ps command, {stdout}, {stderr}"
    assert "tmate-ssh-server" in stdout, "tmate-ssh-server service is not running"
