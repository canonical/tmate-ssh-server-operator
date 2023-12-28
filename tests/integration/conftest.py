# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for tmate-ssh-server charm integration tests."""
import logging
import typing

import pytest
import pytest_asyncio
from helpers import wait_for
from juju.application import Application
from juju.client._definitions import DetailedStatus, FullStatus, MachineStatus
from juju.machine import Machine
from juju.model import Model
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def model(ops_test: OpsTest) -> Model:
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


@pytest.fixture(scope="module", name="github_runner_charm")
async def github_runner_charm_fixture(request: pytest.FixtureRequest) -> str:
    """The path to GitHub Runner charm."""
    charm = request.config.getoption("--github-runner-charm-file")
    charm = f"./{charm}"

    return charm


@pytest_asyncio.fixture(scope="module", name="tmate_ssh_server")
async def tmate_ssh_server_fixture(model: Model, charm: str):
    """The tmate-ssh-server application fixture."""
    app = await model.deploy(charm)
    await model.wait_for_idle(apps=[app.name], wait_for_active=True)
    return app


@pytest_asyncio.fixture(scope="module", name="github_runner")
async def github_runner_fixture(
    model: Model, github_runner_charm: str, request: pytest.FixtureRequest
):
    """The GitHub runner application fixture."""
    pat = request.config.getoption("--pat")
    path = request.config.getoption("--path")
    app = await model.deploy(
        github_runner_charm,
        constraints="cores=4 mem=16G root-disk=20G virt-type=virtual-machine",
        config={
            "token": pat,
            "path": path,
        },
    )
    return app


@pytest_asyncio.fixture(scope="module", name="relate_tmate_github")
async def relate_tmate_github_fixture(
    model: Model, tmate_ssh_server: Application, github_runner: Application
):
    """Relate tmate-ssh-server and GitHub runner charms."""
    await tmate_ssh_server.add_relation("debug-ssh", github_runner.charm_name)
    await model.wait_for_idle(apps=[tmate_ssh_server.charm_name, github_runner.charm_name])


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
