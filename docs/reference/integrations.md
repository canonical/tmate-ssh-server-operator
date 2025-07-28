# Integrations

### agent

_Interface_: debug-ssh
_Supported charms_: [GitHub Runner](https://charmhub.io/github-runner)

The `debug-ssh` relation provides ssh information to the runner machines, allowing it to
automatically configure ssh debug access with tools such as
[action-tmate](https://github.com/canonical/action-tmate).

Example debug-ssh relate command: `juju relate tmate-ssh-server github-runner`