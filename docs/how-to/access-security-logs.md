# How to access security logs

The tmate SSH server charm emits [OWASP](https://owasp.org/)-structured security
event logs for auditing. Each event is a JSON object nested under an `owasp_event`
key, carrying `type: "security"` and `appid: "canonical.tmate-ssh-server"`.

The charm currently emits the following security events:

| Event | When |
|-------|------|
| `sys_startup:<unit>` | The tmate SSH server daemon is started during charm installation. |
| `sys_restart:<unit>` | The daemon is found not running during a status check and is restarted. |
| `authz_admin:<unit>,get-server-config` | The server configuration (host and SSH key fingerprints) is disclosed via the `get-server-config` Juju action. |

## Forwarding path

All of these events are emitted from the charm's Python hook process and are
written to `juju-log`, which Juju forwards to the Juju controller. Their onward
handling, retention, and forwarding to a SIEM is therefore the responsibility of
the Juju controller operator rather than this charm.

## Inspecting events

Security events are visible on the controller with `juju debug-log`:

```
juju debug-log --include unit-tmate-ssh-server-0 | grep owasp_event
```

## Access control

To satisfy least-privilege, read access to these events should be decoupled from
Juju operational rights. The `get-server-config` action discloses the server
configuration and remains governed by Juju RBAC; it must not be exposed to a
read-only log-viewer role. Viewing that an `authz_admin:...,get-server-config`
event *occurred* is a read-only audit capability, whereas running the action
requires Juju privileges.
