# tmate-k8s-operator

A [Juju](https://juju.is/) [charm](https://juju.is/docs/olm/charmed-operators)
deploying and managing [Tmate self-hosted server](https://tmate.io/) on Kubernetes. Tmate is an
open source terminal multiplexer, providing instant terminal sharing capabilities.

Tmate is a terminal multiplexer that allows remote terminal sharing. It enables users to share
their terminal session with other users over the internet, allowing them to collaborate, provide
technical support, or demonstrate commands and procedures in real-time.

This charm provides the tmate-ssh-server service, and when paired with the tmate client provides
self-hosted ssh relay server.

For DevOps and SRE teams, this charm will make operating self hosted tmate-ssh-server simple and
straightforward through Juju's clean interface. Allowing machine relations to the
[Github runner](https://charmhub.io/github-runner), it supports SSH debug access to the running
machines.


## Project and community

The tmate-ssh-server-k8s Operator is a member of the Ubuntu family. It's an open source
project that warmly welcomes community projects, contributions, suggestions,
fixes and constructive feedback.
* [Code of conduct](https://ubuntu.com/community/code-of-conduct)
* [Get support](https://discourse.charmhub.io/)
* [Join our online chat](https://chat.charmhub.io/charmhub/channels/charm-dev)
* [Contribute](https://charmhub.io/jenkins-k8s/docs/contributing)
* [Getting Started](https://charmhub.io/tmate-ssh-server-k8s/docs/getting-started)
Thinking about using the tmate-ssh-server-k8s Operator for your next project? 
[Get in touch](https://chat.charmhub.io/charmhub/channels/charm-dev)!

---

For further details,
[see the charm's detailed documentation](https://charmhub.io/tmate-ssh-server-k8s/docs).

## Generating src docs for every commit

Run the following command:

```bash
echo -e "tox -e src-docs\ngit add src-docs\n" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```
