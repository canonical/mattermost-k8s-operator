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

output "gateway_api_integrator_app_name" {
  description = "Name of the deployed Gateway API integrator application."
  value       = juju_application.gateway_api_integrator.name
}

output "gateway_route_configurator_app_name" {
  description = "Name of the deployed Gateway route configurator application."
  value       = juju_application.gateway_route_configurator.name
}
