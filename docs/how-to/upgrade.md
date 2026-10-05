# How to upgrade

The Tmate SSH server charm can be upgrade with a [`juju refresh`](https://documentation.ubuntu.com/juju/3.6/reference/juju-cli/list-of-juju-cli-commands/refresh/) command, such as:

```bash
juju refresh tmate-ssh-server
```

The charm is stateless and does not rely on storage such as databases, therefore there is no additional work beyond upgrading the charm revision.

The upgrade hook reloads the `systemd` service and restarts the workload using the
image referenced by the new charm revision. Existing SSH host keys are preserved.
The restart interrupts active tmate sessions; schedule the upgrade accordingly.
