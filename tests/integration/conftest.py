# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for tmate-ssh-server charm integration tests."""
import logging
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


@pytest_asyncio.fixture(scope="module", name="tmate_machine")
async def ssh_machine_fixture(model: Model, ops_test: OpsTest):
    """A machine to test tmate ssh connection."""
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
    logger.info("Installing tmate.")
    (retcode, _, stderr) = await ops_test.juju(
        "ssh", str(machine.entity_id), "sudo apt install -y tmate"
    )
    assert retcode == 0, f"Failed to run apt install, {stderr}"
    return machine


@pytest.fixture(scope="module", name="unit")
def unit_fixture(tmate_ssh_server: Application):
    """The tmate ssh server unit."""
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
    return action.results["tmate-config"]


@pytest.fixture(scope="module", name="pub_key")
def pub_key_fixture():
    """The public key contents for ssh access."""
    pub_key_path = Path(Path.home() / ".ssh/id_rsa.pub")
    pub_key_contents = pub_key_path.read_text(encoding="utf-8")
    return pub_key_contents
