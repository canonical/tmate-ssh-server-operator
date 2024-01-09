#!/bin/bash

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

# Pre-run script for integration test operator-workflows action.
# https://github.com/canonical/operator-workflows/blob/main/.github/workflows/integration_test.yaml

# The runner has ~/.ssh dir owned by Docker, change the ownership for ssh access.
sudo mkdir -p ~/.ssh
sudo chown -R runner:runner ~/.ssh
