# Copyright 2023 Canonical Ltd.
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
    # The GitHub Runner operator charm file.
    parser.addoption("--github-runner-charm-file", action="store", default="")
    # The GitHub Personal Access Token.
    parser.addoption("--pat", action="store", default="")
    # The GitHub repository path <owner>/<repo>.
    parser.addoption("--path", action="store", default="")
