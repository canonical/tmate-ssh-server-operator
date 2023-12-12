# Contributing

Build the OCI image:

```bash
cd tmate_ssh_server_rock
rockcraft pack
```

Push the OCI image to microk8s:

```bash
sudo /snap/rockcraft/current/bin/skopeo \
    --insecure-policy \
    copy oci-archive:tmate_ssh_server_rock/tmate-ssh-server_1.0_amd64.rock \
    docker-daemon:tmate_ssh_server:1.0
sudo docker tag tmate-ssh-server:1.0 localhost:32000/tmate-ssh-server:1.0
sudo docker push localhost:32000/tmate-ssh-server:1.0
```

Deploy the charm:

```bash
charmcraft pack
juju deploy ./tmate-ssh-server-k8s-operator_ubuntu-22.04-amd64.charm \
    --resource tmate-ssh-server-image=localhost:32000/tmate-ssh-server:1.0
```

## Generating src docs for every commit

Run the following command:

```bash
echo -e "tox -e src-docs\ngit add src-docs\n" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```
