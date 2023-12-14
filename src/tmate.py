# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Functions to operate tmate-ssh-server."""

from pathlib import Path

SSH_PORT = 10022
USER = "_daemon_"
GROUP = "_daemon_"
EXECUTABLE_DIR = Path("/srv/tmate-ssh-server/")
