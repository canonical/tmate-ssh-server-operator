# How to upgrade

The Tmate SSH server charm can be upgrade with a [`juju refresh`](https://documentation.ubuntu.com/juju/3.6/reference/juju-cli/list-of-juju-cli-commands/refresh/) command, such as:

```bash
juju refresh tmate-ssh-server
```

The charm is stateless and does not rely on storage such as databases, therefore there is not additional work beyond upgrading the charm revision.
