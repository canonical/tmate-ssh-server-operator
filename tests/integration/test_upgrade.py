# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for upgrading the tmate-ssh-server charm."""

import logging

from juju.application import Application
from juju.model import Model
from juju.unit import Unit
from ops import ActiveStatus
from pytest_operator.plugin import OpsTest

from tmate import IMAGE, TMATE_SSH_SERVER_SERVICE_PATH

from .helpers import wait_for

logger = logging.getLogger(__name__)

# Edge revisions built before the upgrade fix, running the legacy 0.1.1 image, by series.
BASELINE_REVISIONS = {"jammy": 43, "noble": 44}


async def test_upgrade_running_unit(ops_test: OpsTest, model: Model, charm: str, codename: str):
    """
    arrange: given a legacy unit from a published revision and an unmanaged tmate container.
    act: when the unit is refreshed to the charm under test, then refreshed to it again.
    assert: one container runs the image from the new unit, the unmanaged container is gone, and
        the second refresh, which does not change the unit, keeps that container running.
    """
    app = await model.deploy(
        "tmate-ssh-server",
        application_name="tmate-upgrade",
        channel="latest/edge",
        revision=BASELINE_REVISIONS[codename],
        series=codename,
    )
    await model.wait_for_idle(apps=[app.name], status=ActiveStatus.name)
    unit: Unit = app.units[0]
    retcode, stdout, stderr = await ops_test.juju(
        "ssh", unit.entity_id, "--", "docker ps --format '{{.Image}}'"
    )
    assert retcode == 0, f"Error running docker ps command, {stdout}, {stderr}"
    assert IMAGE not in stdout.split(), "Baseline already runs the charm's image"
    # A tmate container started outside the charm, for example by hand, gets a Docker-generated
    # name that the service unit does not track.
    retcode, stdout, stderr = await ops_test.juju(
        "ssh",
        unit.entity_id,
        "--",
        "docker run --detach --entrypoint sleep ghcr.io/canonical/tmate-ssh-server:0.1.1 infinity",
    )
    assert retcode == 0, f"Error starting unmanaged tmate container, {stdout}, {stderr}"

    await _refresh(model, app, charm)

    retcode, stdout, stderr = await ops_test.juju(
        "ssh", unit.entity_id, "--", "docker ps -a --format '{{.ID}} {{.Image}} {{.State}}'"
    )
    assert retcode == 0, f"Error running docker ps command, {stdout}, {stderr}"
    tmate_containers = [line.split() for line in stdout.splitlines() if "tmate-ssh-server" in line]
    assert len(tmate_containers) == 1, f"Expected one tmate container, {tmate_containers}"
    container_id, image, state = tmate_containers[0]
    assert state == "running", f"tmate container is not running, {tmate_containers}"
    retcode, stdout, stderr = await ops_test.juju(
        "ssh", unit.entity_id, "--", f"cat {TMATE_SSH_SERVER_SERVICE_PATH}"
    )
    assert retcode == 0, f"Error reading service unit, {stdout}, {stderr}"
    assert image in stdout, "Running image does not match the service unit"
    assert image == IMAGE, "Running image is not the charm's image"
    retcode, stdout, stderr = await ops_test.juju(
        "ssh", unit.entity_id, "--", "systemctl --quiet is-active tmate-ssh-server"
    )
    assert retcode == 0, f"tmate-ssh-server service is not running, {stdout}, {stderr}"

    await _refresh(model, app, charm)

    retcode, stdout, stderr = await ops_test.juju(
        "ssh", unit.entity_id, "--", "docker ps --format '{{.ID}} {{.Image}}'"
    )
    assert retcode == 0, f"Error running docker ps command, {stdout}, {stderr}"
    assert f"{container_id} {image}" in stdout.splitlines(), "Unchanged unit restarted workload"


async def _refresh(model: Model, app: Application, charm: str) -> None:
    """Refresh the application to a local charm and wait for the upgrade to settle.

    Args:
        model: The model hosting the application.
        app: The application to refresh.
        charm: The path of the charm to refresh to.
    """

    async def charm_rev() -> int | None:
        """Get the application's current charm revision.

        Returns:
            The charm revision reported by the model status, if the application is listed.
        """
        status = await model.get_status()
        app_status = status.applications[app.name]
        return app_status.charm_rev if app_status else None

    previous_rev = await charm_rev()
    logger.info("Refreshing %s from revision %s.", app.name, previous_rev)
    await app.refresh(path=charm)

    async def upgraded() -> bool:
        """Check whether the application runs a new charm revision.

        Returns:
            True once the charm revision changed.
        """
        return await charm_rev() != previous_rev

    await wait_for(upgraded, timeout=60 * 10)
    await model.wait_for_idle(apps=[app.name], status=ActiveStatus.name)
