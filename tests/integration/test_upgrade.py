# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for upgrading the tmate-ssh-server charm."""

import logging

from juju.model import Model
from juju.unit import Unit
from ops import ActiveStatus
from pytest_operator.plugin import OpsTest

from tmate import TMATE_SSH_SERVER_SERVICE_PATH

from .helpers import wait_for

logger = logging.getLogger(__name__)


async def test_upgrade_running_unit(ops_test: OpsTest, model: Model, charm: str, codename: str):
    """
    arrange: given a running unit deployed from the published edge charm.
    act: when the unit is refreshed to the charm under test.
    assert: the previous container is removed and the service runs the image from the new unit.
    """
    app = await model.deploy(
        "tmate-ssh-server",
        application_name="tmate-upgrade",
        channel="latest/edge",
        series=codename,
    )
    await model.wait_for_idle(apps=[app.name], status=ActiveStatus.name)
    unit: Unit = app.units[0]
    previous_containers = await _running_containers(ops_test, unit)
    assert len(previous_containers) == 1, f"Expected one tmate container, {previous_containers}"

    logger.info("Refreshing %s to the charm under test.", app.name)
    await app.refresh(path=charm)

    async def replaced() -> bool:
        """Check whether a new container replaced the previous one.

        Returns:
            True if the running containers no longer match the previous ones.
        """
        running = await _running_containers(ops_test, unit)
        return bool(running) and running != previous_containers

    await wait_for(replaced, timeout=60 * 10)
    await model.wait_for_idle(apps=[app.name], status=ActiveStatus.name)

    running_containers = await _running_containers(ops_test, unit)
    assert len(running_containers) == 1, f"Expected one tmate container, {running_containers}"
    previous_name = previous_containers[0][0]
    retcode, stdout, stderr = await ops_test.juju(
        "ssh", unit.entity_id, "--", "docker ps -a --format '{{.Names}}'"
    )
    assert retcode == 0, f"Error running docker ps command, {stdout}, {stderr}"
    assert previous_name not in stdout.split(), "Previous tmate container was not removed"
    retcode, stdout, stderr = await ops_test.juju(
        "ssh", unit.entity_id, "--", f"cat {TMATE_SSH_SERVER_SERVICE_PATH}"
    )
    assert retcode == 0, f"Error reading service unit, {stdout}, {stderr}"
    assert running_containers[0][1] in stdout, "Running image does not match the service unit"
    retcode, stdout, stderr = await ops_test.juju(
        "ssh", unit.entity_id, "--", "systemctl --quiet is-active tmate-ssh-server"
    )
    assert retcode == 0, f"tmate-ssh-server service is not running, {stdout}, {stderr}"


async def _running_containers(ops_test: OpsTest, unit: Unit) -> list[tuple[str, str]]:
    """List the running tmate-ssh-server containers on the unit.

    Args:
        ops_test: The pytest-operator test helper.
        unit: The unit to inspect.

    Returns:
        The (name, image) pairs of running tmate-ssh-server containers.

    Raises:
        RuntimeError: if docker ps fails on the unit.
    """
    retcode, stdout, stderr = await ops_test.juju(
        "ssh", unit.entity_id, "--", "docker ps --format '{{.Names}} {{.Image}}'"
    )
    if retcode != 0:
        raise RuntimeError(f"Error running docker ps command, {stdout}, {stderr}")
    return [
        (name, image)
        for name, image in (line.split() for line in stdout.splitlines() if line.strip())
        if "tmate-ssh-server" in image
    ]
