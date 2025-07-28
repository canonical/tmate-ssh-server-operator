# Deploy the Tmate-ssh-server charm for the first time

## What you'll do

- Deploy the [tmate-ssh-server charm](https://charmhub.io/tmate-ssh-server)
- Get the `.tmate.conf` through `get-server-config` action
- Create a `Tmate` client machine and configure `Tmate` client
- SSH into `Tmate` terminal

Tmate is a remote terminal sharing tool that allows users to securely share their terminal with
others in real-time, making it easy to collaborate, troubleshoot, and provide support across
different systems and networks. It provides a seamless way to establish SSH connections and enables
remote access without requiring complex network configurations.

## Requirements

To deploy a tmate-ssh-server charm, you will need a Juju controller bootstrapped with any machine
controller type.
To see how to bootstrap your Juju installation with LXD, please refer to the documentation
on LXD [installation](https://juju.is/docs/juju/lxd).

## Steps
### Set up the tutorial model

To easily clean up the resources and to separate your workload from the contents of this tutorial,
set up a new model with the following command.

```
juju add-model tmate-tutorial
```

### Deploy the tmate-ssh-server charm

Use the following command to deploy the tmate-ssh-server charm.

```
juju deploy tmate-ssh-server
```

### Get the tmate configuration contents

To register a Tmate client, we need a file containing the configuration details.
Use the `get-server-config` action to retrieve the details, and save the output contents
into `.tmate.conf` for later use.

```
juju run tmate-ssh-server/0 get-server-config | grep -E set | sed 's/^[[:space:]]*//' > .tmate.conf
```

The output of `.tmate.conf` file generated from the previous command will look something like the following:
```
set -g tmate-server-host <tmate-ssh-server-unit-ip>
set -g tmate-server-port 10022
set -g tmate-server-rsa-fingerprint <rsa-fingerprint>
set -g tmate-server-ed25519-fingerprint <ed25519-fingerprint>
```

### Create a tmate client machine

To imitate a `Tmate` client, we can add a machine on Juju and install `Tmate`.

```
juju add-machine
juju ssh 1 -- "sudo apt update && sudo apt install -y tmate"
```

Copy the `.tmate.conf` file we previously created to the client
machine.

Then, register the public key of the current machine (use `ssh-keygen` to generate key files if
none exist yet).

```
juju scp .tmate.conf 1:~/.tmate.conf
juju ssh 1 -- "echo $(~/.ssh/id_rsa.pub) >> ~/.ssh/authorized_keys"
```

Start the Tmate client and get the SSH command.
```
# start a new tmate session
juju ssh 1 -- "tmate -a ~/.ssh/authorized_keys -S /tmp/tmate.sock new-session -d"
# wait until the tmate session is ready
juju ssh 1 -- "tmate -S /tmp/tmate.sock wait tmate-ready"
# print tmate ssh details
juju ssh 1 -- "tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}'"
# output looks something like ssh -p10022 <user>@0.0.0.0
```

### SSH into the tmate terminal

Run `juju status` command to find out the unit IP address.

```
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
ssh <user>@<unit-ip>
```

The output will look something like the following:

```
Tip: if you wish to use tmate only for remote access, run: tmate -F
To see the following messages again, run in a tmate session: tmate show-messages
Press <q> or <ctrl-c> to continue
---------------------------------------------------------------------
Connecting to <unit-ip>...
Note: clear your terminal before sharing readonly access
ssh session read only: ssh -p10022 ro-<ro-user>@<unit-ip>
ssh session: ssh -p10022 <user>@<unit-ip>
```


### Clean up the environment

Congratulations! You have successfully finished the tmate-ssh-server tutorial. You can now remove
the `.tmate.conf` file and the Juju model environment that you’ve created using the following
command.

```
rm .tmate.conf
juju destroy-model tmate-tutorial -y
```
