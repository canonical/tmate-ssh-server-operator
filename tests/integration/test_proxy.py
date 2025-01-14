# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for tmate-ssh-server charm."""
import logging

from juju.machine import Machine
from juju.model import Model
from juju.unit import Unit
from pytest_operator.plugin import OpsTest

from .helpers import wait_for

logger = logging.getLogger(__name__)


async def test_proxy(
    ops_test: OpsTest,
    model: Model,
    charm: str,
    proxy_machine: Machine,
    machine_ip: str,
):
    """
    arrange: given a model configured with squid proxy ip address.
    act: when tmate charm is deployed.
    assert: proxy log contains docker access.
    """
    await model.set_config(
        {
            "juju-http-proxy": f"http://{machine_ip}:3218",
            "juju-https-proxy": f"http://{machine_ip}:3218",
        }
    )

    logger.info("Deploying tmate charm.")
    app = await model.deploy(charm)
    await model.wait_for_idle(apps=[app.name], wait_for_active=True)
    unit: Unit = next(iter(app.units))

    async def wait_for_access_log() -> bool:
        """Wait until access log contains proxy access logs from tmate charm to docker.

        Returns:
            Whether ghcr.io access was found in proxy log.
        """
        (retcode, stdout, stderr) = await ops_test.juju(
            "ssh", proxy_machine.entity_id, "sudo cat /var/log/squid/access.log"
        )
        assert retcode == 0, f"Failed read squid access log, {stdout} {stderr}"
        logger.info("Squid access log: %s", stdout)
        return unit.public_address in stdout and "ghcr.io" in stdout

    await wait_for(wait_for_access_log)
