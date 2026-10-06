# How to upgrade

The Tmate SSH server charm can be upgrade with a [`juju refresh`](https://documentation.ubuntu.com/juju/3.6/reference/juju-cli/list-of-juju-cli-commands/refresh/) command, such as:

```bash
juju refresh tmate-ssh-server
```

The charm is stateless and does not rely on storage such as databases, therefore there is no additional work beyond upgrading the charm revision.

When the new charm revision changes the workload's `systemd` service, for
example its image, the upgrade hook pulls the new image, then removes the
running workload container and restarts the workload with the new service. If
the image cannot be pulled, the hook fails and the current workload keeps
running. Existing SSH host keys are preserved.
This restart interrupts active tmate sessions; schedule such upgrades accordingly.
Upgrades that leave the service unchanged keep the workload running.
