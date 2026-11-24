# Contributing

Deploy the charm:

```bash
charmcraft pack
juju deploy ./tmate-ssh-server-operator_ubuntu-22.04-amd64.charm \
    --constraints="virt-type=virtual-machine"
```

## Publish the tmate SSH server image

The charm publication workflow does not publish the image referenced by
`IMAGE` in `src/tmate.py`. A maintainer with write access to the GitHub
Container registry package must publish it before merging a change to that
tag.

1. Set the `version` in `tmate-ssh-server_rock/rockcraft.yaml` and the tag of
   `IMAGE` in `src/tmate.py` to the same new value.
2. Build the rock from a clean environment, so Ubuntu packages and the Pebble
   snap are refreshed:

   ```bash
   cd tmate-ssh-server_rock
   rockcraft clean
   rockcraft pack
   ```

3. Log in to the registry and publish the rock, replacing `<version>`:

   ```bash
   rockcraft.skopeo login ghcr.io
   rockcraft.skopeo copy \
       oci-archive:tmate-ssh-server_<version>_amd64.rock \
       docker://ghcr.io/canonical/tmate-ssh-server:<version>
   ```

4. Check that the published tag can be pulled anonymously before merging:

   ```bash
   rockcraft.skopeo inspect --no-creds docker://ghcr.io/canonical/tmate-ssh-server:<version>
   ```
