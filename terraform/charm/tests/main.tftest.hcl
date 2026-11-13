# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "basic_deploy" {
  variables {
    model_uuid = run.setup_tests.model_uuid
    base       = "ubuntu@24.04"
    channel    = "latest/edge"
    # renovate: depName="tmate-ssh-server"
    revision = 50
  }

  assert {
    condition     = output.application.name == "tmate-ssh-server"
    error_message = "tmate-ssh-server application name did not match expected"
  }

  assert {
    condition     = output.provides.debug_ssh.endpoint == "debug-ssh"
    error_message = "tmate-ssh-server module should provide 'provides.debug_ssh' output"
  }
}
