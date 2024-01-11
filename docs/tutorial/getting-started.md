# Getting Started

## What you'll do

- Deploy the [tmate-ssh-server charm](https://charmhub.io/tmate-ssh-server)
- Get the .tmate.conf through `get-server-config` action
- Create a tmate client machine and configure tmate client
- SSH into tmate terminal

Tmate is a remote terminal sharing tool that allows users to securely share their terminal with
others in real-time, making it easy to collaborate, troubleshoot, and provide support across
different systems and networks. It provides a seamless way to establish SSH connections and enables
remote access without requiring complex network configurations.

### Prerequisites

To deploy a tmate-ssh-server charm, you will need a juju bootstrapped with any machine controller.
To see how to bootstrap your juju installation with LXD, please refer to the documentation
on LXD [installation](https://juju.is/docs/juju/lxd).

### Setting up the tutorial model

To easily clean up the resources and to separate your workload from the contents of this tutorial,
it is recommended to set up a new model with the following command.

```
$ juju add-model tmate-tutorial
```

### Deploy the tmate-ssh-server charm

Use the following command to deploy the tmate-ssh-server charm.

```
$ juju deploy tmate-ssh-server
```

### Get the tmate configuration contents

To get the contents of `.tmate.conf` file to register a tmate client, use the `get-server-config`
action to retrieve the configuration details. Save the output contents into `.tmate.conf` file for
later use.
```
$ juju run tmate-ssh-server/0 get-server-config | grep -E set | sed 's/^[[:space:]]*//' > .tmate.conf
```

The output of .tmate.conf file generated from the command above will look something like the following:
```
$ cat .tmate.conf
set -g tmate-server-host <tmate-ssh-server-unit-ip>
set -g tmate-server-port 10022
set -g tmate-server-rsa-fingerprint <rsa-fingerprint>
set -g tmate-server-ed25519-fingerprint <ed25519-fingerprint>
```

### Create a tmate client machine

To immitate a tmate client, we can add a machine on Juju and install tmate.

```
$ juju add-machine
created machine 1

$ juju ssh 1 -- "sudo apt update && sudo apt install -y tmate"
```

Copy the .tmate.conf file retrieved from the
[Get the tmate configuration contents](#get-the-tmate-configuration-contents) above to the client
machine.

Then, register the public key of the current machine (use `ssh-keygen` to generate key files if
none exist yet).

```
$ juju scp .tmate.conf 1:~/.tmate.conf
$ juju ssh 1 -- "echo $(~/.ssh/id_rsa.pub) >> ~/.ssh/authorized_keys"
```

Start the tmate client & get the ssh command.
```
# start a new tmate session
$ juju ssh 1 -- "tmate -a ~/.ssh/authorized_keys -S /tmp/tmate.sock new-session -d"
# wait until the tmate session is ready
$ juju ssh 1 -- "tmate -S /tmp/tmate.sock wait tmate-ready"
# print tmate ssh details
$ juju ssh 1 -- "tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'"
ssh -p10022 <token>@0.0.0.0
```

### SSH into the tmate terminal

Use `juju status` command to find out the unit ip address.

```
$ juju status
Model           Controller  Cloud/Region         Version  SLA          Timestamp
tmate-tutorial  localhost   localhost/localhost  3.1.6    unsupported  <timestamp>

App               Version  Status  Scale  Charm             Channel  Rev  Exposed  Message
tmate-ssh-server           active      1  tmate-ssh-server             0  no       

Unit                 Workload  Agent  Machine  Public address  Ports  Message
tmate-ssh-server/0*  active    idle   0        <unit-ip>          

Machine  State    Address              Inst id        Base          AZ  Message
0        started  <unit-ip>            juju-92dc13-0  ubuntu@22.04      Running
1        started  <client-machine-ip>  juju-92dc13-1  ubuntu@22.04      Running
```

Then use the ssh command output from the previous step and replace `0.0.0.0` address to the unit
IP of tmate-ssh-server unit.

```
$ ssh <token>@<unit-ip>

Tip: if you wish to use tmate only for remote access, run: tmate -F
To see the following messages again, run in a tmate session: tmate show-messages
Press <q> or <ctrl-c> to continue
---------------------------------------------------------------------
Connecting to <unit-ip>...
Note: clear your terminal before sharing readonly access
ssh session read only: ssh -p10022 ro-<ro-token>@<unit-ip>
ssh session: ssh -p10022 <token>@<unit-ip>
```


### Cleaning up the environment

Congratulations! You have successfully finished the tmate-ssh-server tutorial. You can now remove
the `.tmate.conf` file and the juju model environment that you’ve created using the following
command.

```
$ rm .tmate.conf
$ juju destroy-model tmate-tutorial -y
```
