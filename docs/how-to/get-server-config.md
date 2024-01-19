# How to get server config

### Get server config

To retrieve the server configuration for tmate client (contents of `.tmate.conf`), run the
following action.

```
juju run tmate-ssh-server/0 get-server-config
```

The output should look similar to the contents below:

```
Running operation 1 with 1 task
  - task 1 on unit-tmate-ssh-server-0

Waiting for task 1...
tmate-config: |2

  set -g tmate-server-host <unit-ip>
  set -g tmate-server-port 10022
  set -g tmate-server-rsa-fingerprint <rsa-fingerprint>
  set -g tmate-server-ed25519-fingerprint <ed25519-fingerprint>
```

You can use the output above as the tmate configuration file (`.tmate.conf`) contents on a tmate
client machine.
