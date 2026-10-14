# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "application" {
  description = "The deployed application object."
  value       = juju_application.tmate_ssh_server
}

output "provides" {
  description = "Map of the provided integration endpoints."
  value = {
    debug_ssh = {
      kind     = "endpoint"
      name     = juju_application.tmate_ssh_server.name
      endpoint = "debug-ssh"
    }
  }
}

output "requires" {
  description = "Map of the required integration endpoints."
  value       = {}
}
