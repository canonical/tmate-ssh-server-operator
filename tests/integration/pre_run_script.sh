#!/bin/bash

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

# Pre-run script for integration test operator-workflows action.
# https://github.com/canonical/operator-workflows/blob/main/.github/workflows/integration_test.yaml

# The runner has ~/.ssh dir owned by Docker, change the ownership for ssh access.
sudo mkdir -p ~/.ssh
sudo chown -R runner:runner ~/.ssh

wait_time=5
max_attempts=10
attempt=1

while [[ $attempt -le $max_attempts ]]; do
  if [[ -f "$~/.ssh/id_rsa" ]]; then
    echo "id_rsa found!"
    break
  fi

  echo "id_rsa not found. Attempt $attempt of $max_attempts. Waiting for $wait_time seconds..."
  sleep $wait_time
  attempt=$((attempt + 1))
done

if [[ $attempt -gt $max_attempts ]]; then
  echo "Timeout. id_rsa not found after $((max_attempts * wait_time)) seconds."
fi
