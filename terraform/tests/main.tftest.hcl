# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variables {
  channel = "latest/edge"
  # renovate: depName="__charm_name__"
  revision = 1
}

run "basic_deploy" {
  assert {
    condition     = module.__charm_name__.app_name == "__charm_name__"
    error_message = "__charm_name__ app_name did not match expected"
  }
}
