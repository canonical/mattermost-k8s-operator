# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "mattermost_app_name" {
  description = "Name of the deployed Mattermost application."
  value       = module.mattermost.app_name
}

output "postgresql_app_name" {
  description = "Name of the deployed PostgreSQL application."
  value       = juju_application.postgresql.name
}

output "ingress_configurator" {
  description = "Ingress configurator module outputs."
  value       = module.ingress_configurator
}
