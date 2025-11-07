# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Helpers for tmate-ssh-server-operator charm integration tests."""

import inspect
import time
import typing

from juju.machine import Machine


def get_machine_ip_address(machine: Machine) -> typing.Optional[str]:
    """Get latest machine IP address.

    Returns:
        The latest machine IP address if ready, None otherwise.
    """
    latest_machine = machine.latest()
    addresses = latest_machine.data["addresses"]
    try:
        address = next(
            iter(
                [address["value"] for address in addresses if address["scope"] != "local-machine"]
            )
        )
    except StopIteration:
        return None
    return address


async def wait_for(
    func: typing.Callable[[], typing.Union[typing.Awaitable, typing.Any]],
    timeout: int = 300,
    check_interval: int = 10,
) -> typing.Any:
    """Wait for function execution to become truthy.

    Args:
        func: A callback function to wait to return a truthy value.
        timeout: Time in seconds to wait for function result to become truthy.
        check_interval: Time in seconds to wait between ready checks.

    Raises:
        TimeoutError: if the callback function did not return a truthy value within timeout.

    Returns:
        The result of the function if any.
    """
    deadline = time.time() + timeout
    is_awaitable = inspect.iscoroutinefunction(func)
    while time.time() < deadline:
        if is_awaitable:
            if result := await func():
                return result
        else:
            if result := func():
                return result
        time.sleep(check_interval)

    # final check before raising TimeoutError.
    if is_awaitable:
        if result := await func():
            return result
    else:
        if result := func():
            return result
    raise TimeoutError()
