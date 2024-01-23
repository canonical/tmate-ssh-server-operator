# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for tmate-ssh-server charm integration tests."""
import logging
import secrets
import typing
from pathlib import Path

import pytest
import pytest_asyncio
from juju.action import Action
from juju.application import Application
from juju.client._definitions import DetailedStatus, FullStatus, MachineStatus
from juju.machine import Machine
from juju.model import Model
from juju.unit import Unit
from pytest_operator.plugin import OpsTest

from .helpers import wait_for

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module", name="model")
def model_fixture(ops_test: OpsTest) -> Model:
    """Juju model used in the test."""
    assert ops_test.model is not None
    return ops_test.model


@pytest_asyncio.fixture(scope="module", name="charm")
async def charm_fixture(request: pytest.FixtureRequest, ops_test: OpsTest) -> str:
    """The path to charm."""
    charm = request.config.getoption("--charm-file")
    if not charm:
        charm = await ops_test.build_charm(".")
    else:
        charm = f"./{charm}"

    return charm


@pytest_asyncio.fixture(scope="module", name="tmate_ssh_server")
async def tmate_ssh_server_fixture(model: Model, charm: str):
    """The tmate-ssh-server application fixture."""
    app = await model.deploy(charm)
    await model.wait_for_idle(apps=[app.name], wait_for_active=True)
    return app


@pytest.fixture(scope="module", name="unit")
def unit_fixture(tmate_ssh_server: Application):
    """The tmate-ssh-server unit."""
    unit: Unit = next(iter(tmate_ssh_server.units))
    return unit


@pytest_asyncio.fixture(scope="module", name="tmate_config")
async def tmate_config_fixture(unit: Unit):
    """The .tmate.conf contents."""
    action: Action = await unit.run_action("get-server-config")
    await action.wait()
    assert (
        action.status == "completed"
    ), f"Get server-config action failed, status: {action.status}"
    config = action.results["tmate-config"]
    return config


@pytest.fixture(scope="module", name="pub_key")
def pub_key_fixture():
    """The id_rsa public key fixture to use for ssh authorization."""
    pub_key_path = Path(Path.home() / ".ssh/id_rsa.pub")
    return pub_key_path.read_text(encoding="utf-8")


@pytest_asyncio.fixture(scope="module", name="machine")
async def machine_fixture(model: Model, ops_test: OpsTest):
    """An empty machine to interact with tmate server charm."""
    machine: Machine = await model.add_machine()

    async def wait_machine():
        """Wait for machine to be in running status.

        Returns:
            True if the machine is running, False otherwise.
        """
        status: FullStatus = await model.get_status()
        machine_status: MachineStatus = status.machines[machine.entity_id]
        assert machine_status, f"Failed to get machine {machine.entity_id}"
        # mypy incorrectly assumes dict[Any, Any] | DetailedStatus.
        instance_status = typing.cast(DetailedStatus, machine_status.instance_status)
        logger.info("Waiting for machine to be running... %s", instance_status.status)
        return instance_status.status == "running"

    await wait_for(wait_machine, timeout=60 * 5)

    logger.info("Running update.")
    (retcode, _, stderr) = await ops_test.juju("ssh", str(machine.entity_id), "sudo apt update -y")
    assert retcode == 0, f"Failed to run apt update, {stderr}"
    return machine


@pytest_asyncio.fixture(scope="module", name="tmate_machine")
async def ssh_machine_fixture(ops_test: OpsTest, machine: Machine):
    """A machine to test tmate ssh connection."""
    logger.info("Installing tmate.")
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh",
        str(machine.entity_id),
        "DEBIAN_FRONTEND=noninteractive sudo apt-get install -y tmate",
    )
    assert retcode == 0, f"Failed to run apt install, {stdout} {stderr}"
    return machine


@pytest_asyncio.fixture(scope="module", name="proxy_machine")
async def proxy_machine_fixture(ops_test: OpsTest, machine: Machine):
    """A machine to host squid proxy."""
    logger.info("Installing squid.")
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh",
        str(machine.entity_id),
        "DEBIAN_FRONTEND=noninteractive sudo apt-get install -y squid",
    )
    assert retcode == 0, f"Failed to run apt install, {stdout} {stderr}"
    squid_config = """
http_port 0.0.0.0:3218

cache_mem 8 MB

maximum_object_size 4096 KB

cache_dir ufs /var/spool/squid 100 16 256

cache_access_log /var/log/squid/access.log
cache_log /var/log/squid/cache.log
cache_store_log /var/log/squid/store.log

http_access allow all
http_access deny all"""
    temp_config_file_path = Path(f"./{secrets.token_hex(8)}")
    temp_config_file_path.write_text(squid_config, encoding="utf-8")
    (retcode, stdout, stderr) = await ops_test.juju(
        "scp", temp_config_file_path.name, f"{machine.entity_id}:~/squid.conf"
    )
    assert retcode == 0, f"Failed to scp squid conf file {stdout} {stderr}"
    temp_config_file_path.unlink()
    # cannot scp directly to /etc due to permission error
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh", str(machine.entity_id), "sudo mv ~/squid.conf /etc/squid/squid.conf"
    )
    assert retcode == 0, f"Failed to move squid conf file {stdout} {stderr}"
    (retcode, stdout, stderr) = await ops_test.juju(
        "ssh", str(machine.entity_id), "sudo systemctl restart squid.service"
    )
    assert retcode == 0, f"Failed to restart squid service, {stdout} {stderr}"
    return machine


@pytest_asyncio.fixture(scope="module", name="machine_ip")
async def machine_ip_fixture(machine: Machine) -> str:
    """The machine public IP address."""

    def get_machine_ip_address():
        """Get latest machine IP address."""
        latest_machine = machine.latest()
        addresses = latest_machine.data["addresses"]
        try:
            address = next(
                iter(
                    [
                        address["value"]
                        for address in addresses
                        if address["scope"] != "local-machine"
                    ]
                )
            )
        except StopIteration:
            return None
        return address

    await wait_for(get_machine_ip_address)

    return get_machine_ip_address()
