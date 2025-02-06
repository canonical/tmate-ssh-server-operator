# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for tmate-ssh-server charm tests."""

import pytest


def pytest_addoption(parser: pytest.Parser):
    """Parse additional pytest options.

    Args:
        parser: pytest command line parser.
    """
    # The prebuilt charm file.
    parser.addoption("--charm-file", action="store", default="")
    # Allow tmate-ssh-server-image input argument to be passed on by operator-workflows.
    parser.addoption("--tmate-ssh-server-image", action="store", default="")
