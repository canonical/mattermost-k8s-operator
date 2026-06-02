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
  description = "Ingress configurator outputs."
  value = {
    app_name = juju_application.ingress_configurator.name
    endpoints = {
      ingress       = "ingress"
      haproxy_route = "haproxy-route"
    }
  }
}
