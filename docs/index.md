<!-- vale Canonical.007-Headings-sentence-case = NO -->
# Tmate SSH server operator
<!-- vale Canonical.007-Headings-sentence-case = YES -->

A [Juju](https://juju.is/) [charm](https://documentation.ubuntu.com/juju/3.6/reference/charm/)
deploying and managing [Tmate self-hosted server](https://github.com/tmate-io/tmate). Tmate is an
open source terminal multiplexer, providing instant terminal sharing capabilities.

Tmate enables users to share their terminal session with other users over the internet, allowing
them to collaborate, provide technical support, or demonstrate commands and procedures in
real-time.

This charm provides the tmate SSH server service, which is paired with the tmate client to provide
a self-hosted SSH relay server.

For DevOps and SRE teams, this charm will make operating a self-hosted tmate SSH server simple and
straightforward through Juju's clean interface. Through its integration with the
[GitHub runner](https://charmhub.io/github-runner) charm, it provides SSH debug access to the
runner VMs managed by that charm.

## In this documentation

|                 |                                                                                                                                                                      |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Get started** | [Deploy the tmate SSH server charm for the first time](tutorial/getting-started.md)                                                                                  |
| **Operations**  | [Get server config](how-to/get-server-config.md) \| [Upgrade](how-to/upgrade.md) \| [Actions](reference/actions.md) \| [Configurations](reference/configurations.md) |
| **Relations**   | [Relation endpoints](reference/relations.md)                                                                                                                         |
| **Design**      | [Charm architecture](reference/charm-architecture.md) \| [Port number](explanation/port-number.md)                                                                   |

## How this documentation is organized

This documentation uses the [Diátaxis documentation structure](https://diataxis.fr/).

- The [Tutorial](tutorial) takes you step-by-step through deploying the tmate SSH server charm and
  sharing your first terminal session.
- The [How-to guides](how-to) cover practical tasks such as retrieving the server configuration
  for the tmate client and upgrading the charm.
- [Reference](reference) provides technical details on actions, configurations, relation
  endpoints, and the charm architecture.
- [Explanation](explanation) includes context on design choices such as the SSH port number.

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
  1. [Charm architecture](reference/charm-architecture.md)
  1. [Configurations](reference/configurations.md)
  1. [Integrations](reference/relations.md)
1. [Explanation](explanation)
  1. [Port Number](explanation/port-number.md)
