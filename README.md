# Tmate SSH server operator
<!-- Use this space for badges -->

A Juju charm that provides the self-hosted GitHub runner an integration with self-hosted SSH debug
server. The self-hosted SSH debug server is automatically available via the forked version of 
[action-tmate](https://github.com/canonical/action-tmate). By default, the connection is allowed
only for the actor of the debug workflow for security considerations. This charm is deployed as a
VM.

Like any Juju charm, this charm supports one-line deployment, integration, scaling, and more. For
Charmed Tmate SSH server, there are no configurations required and the charm works out of the box.

For information about how to deploy, integrate, and manage this charm, see the Official 
[CharmHub Documentation](https://charmhub.io/tmate-ssh-server).

## Get started
<!--Briefly summarize what the user will achieve in this guide.-->
Deploy Tmate SSH server with GitHub runners.

<!--Indicate software and hardware prerequisites-->
You'll need a working [OpenStack installation](https://microstack.run/docs/single-node) to deploy
the GitHub runners on.

### Set up

Follow [MicroStack's single-node](https://microstack.run/docs/single-node) starting guide to set 
up MicroStack.

Follow the [tutorial on GitHub runner](https://charmhub.io/github-runner) to deploy the GitHub
runner.

### Deploy

Deploy the charm.

```
juju deploy tmate-ssh-server

juju integrate tmate-ssh-server github-runner
```

### Basic operations
<!--Brief walkthrough of performing standard configurations or operations-->

After having deployed and integrated the charm with the GitHub runner charm, the SSH connection to
the runner VM should be accessible via [action-tmate](https://github.com/canonical/action-tmate).
To find out more about how to configure the workflow, refer to the [Getting Started](https://github.com/canonical/action-tmate?tab=readme-ov-file#getting-started) section of action tmate.

## Integrations
<!-- Information about particularly relevant interfaces, endpoints or libraries related to the charm. For example, peer relation endpoints required by other charms for integration.--> 
* debug-ssh: Provides GitHub runners with addresses to connect to for action-tmate.

For a full list of integrations, please refer to the [Charmhub documentation](https://charmhub.io/github-runner-image-builder/integrations).

## Learn more
* [Read more](https://charmhub.io/tmate-ssh-server) <!--Link to the charm's official documentation-->
* [Developer documentation](https://github.com/canonical/tmate-ssh-server-operator/blob/main/CONTRIBUTING.md) <!--Link to any developer documentation-->
* [Troubleshooting](https://matrix.to/#/!DYvOMMMjuXPZRJYHdy:ubuntu.com?via=ubuntu.com&via=matrix.org)

## Project and community
* [Issues](https://github.com/canonical/tmate-ssh-server-operator/issues) <!--Link to GitHub issues (if applicable)-->
* [Contributing](https://github.com/canonical/tmate-ssh-server-operator/blob/main/CONTRIBUTING.md) <!--Link to any contribution guides--> 
* [Matrix](https://matrix.to/#/!DYvOMMMjuXPZRJYHdy:ubuntu.com?via=ubuntu.com&via=matrix.org) <!--Link to contact info (if applicable), e.g. Matrix channel-->
