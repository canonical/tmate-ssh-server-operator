<!-- vale Canonical.007-Headings-sentence-case = NO -->
# Tmate SSH server operator
<!-- vale Canonical.007-Headings-sentence-case = YES -->

A [Juju](https://juju.is/) [charm](https://documentation.ubuntu.com/juju/3.6/reference/charm/)
deploying and managing [Tmate self-hosted server](https://github.com/tmate-io/tmate). tmate is an
open source terminal multiplexer, providing instant terminal sharing capabilities.

Tmate enables users to share their terminal session with other users over the internet, allowing
them to collaborate, provide technical support, or demonstrate commands and procedures in
real-time.

This charm provides the tmate SSH server service, which is paired with the tmate client to provide
a self-hosted SSH relay server.

For DevOps and SRE teams, this charm will make operating self hosted tmate SSH server simple and
straightforward through Juju's clean interface. Allowing machine relations to the
[Github runner](https://charmhub.io/github-runner), it supports SSH debug access to the runner VMs
managed by the charm.

## Project and community

The Tmate SSH server operator is a member of the Ubuntu family. It's an open source project that
warmly welcomes community projects, contributions, suggestions, fixes and constructive feedback.

- [Code of conduct](https://ubuntu.com/community/code-of-conduct)
- [Get support](https://discourse.charmhub.io/)
- [Join our online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
- [Contribute](https://github.com/canonical/tmate-ssh-server-operator/blob/main/CONTRIBUTING.md)

Thinking about using the tmate SSH server operator for your next project?
[Get in touch](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)!

# Contents

1. [Tutorial](tutorial)
  1. [Getting Started](tutorial/getting-started.md)
1. [How to](how-to)
  1. [Get server config](how-to/get-server-config.md)
  1. [Upgrade](how-to/upgrade.md)
1. [Reference](reference)
  1. [Actions](reference/actions.md)
  1. [Charm architecture](reference/charm-architecture.md)  1. [Configurations](reference/configurations.md)
  1. [Integrations](reference/integrations.md)
1. [Explanation](explanation)
  1. [Port Number](explanation/port-number.md)
