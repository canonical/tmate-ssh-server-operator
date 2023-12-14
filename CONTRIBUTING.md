# Contributing

Deploy the charm:

```bash
charmcraft pack
juju deploy ./tmate-ssh-server-operator_ubuntu-22.04-amd64.charm \
    --constraints="virt-type=virtual-machine"
```

## Generating src docs for every commit

Run the following command:

```bash
echo -e "tox -e src-docs\ngit add src-docs\n" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```
