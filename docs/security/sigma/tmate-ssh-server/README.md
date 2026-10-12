# Tmate SSH server Sigma detection rules

Vendor-neutral [Sigma](https://sigmahq.io) rules for the security events emitted by
the `tmate-ssh-server` charm (`appid: canonical.tmate-ssh-server`, `type: security`).
Author once here; convert to your SIEM's query language with `sigma-cli` / pySigma.

## Field mapping (OWASP → Sigma selectors)

The `owasp-logger` library emits each event as a JSON object **nested under an
`owasp_event` key**, so rules select on dotted `owasp_event.*` field names.

| OWASP field | Sigma selector key | Example |
| --- | --- | --- |
| `event` | `owasp_event.event` | `owasp_event.event\|startswith: 'authz_admin'` |
| `level` | `owasp_event.level` | `owasp_event.level: 'WARN'` |
| `appid` | `owasp_event.appid` / `logsource.product` | `canonical.tmate-ssh-server` |

The `event` value is a flat token of the form `<event_name>:<comma-separated-args>`
(for example `sys_restart:tmate-ssh-server/0` or
`authz_admin:tmate-ssh-server/0,get-server-config`), so rules match it with
`startswith` / `contains`.

## Validate & apply

```bash
pip install sigma-cli
sigma check docs/security/sigma/tmate-ssh-server/
# Convert to Loki (LogQL), for example:
sigma convert -t loki docs/security/sigma/tmate-ssh-server/server_config_disclosed.yml
```

## Rules

| File | Event | Detects |
| --- | --- | --- |
| `server_config_disclosed.yml` | `authz_admin` | `get-server-config` action disclosing the server host and SSH key fingerprints |
| `daemon_restart.yml` | `sys_restart` | Self-heal restart of the tmate SSH daemon after it was found not running |
| `daemon_startup.yml` | `sys_startup` | Daemon start during charm installation (audit) |

## Lifecycle

Rules are version-controlled and updated/validated/merged with the product release
cycle. Consumers pull validated rules directly from this directory.
