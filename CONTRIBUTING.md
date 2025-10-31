# Contributing

Deploy the charm:

```bash
charmcraft pack
juju deploy ./tmate-ssh-server-operator_ubuntu-22.04-amd64.charm \
    --constraints="virt-type=virtual-machine"
```
