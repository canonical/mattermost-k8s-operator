# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "mattermost" {
  description = "Mattermost application name and required endpoints."
  value = {
    app_name = module.mattermost.app_name
    requires = module.mattermost.requires
  }
}

output "postgresql_app_name" {
  description = "Name of the deployed PostgreSQL application, if bundled."
  value       = one(juju_application.postgresql[*].name)
}

output "oauth_app_name" {
  description = "Name of the deployed OAuth external IdP integrator application."
  value       = juju_application.oauth_integrator.name
}

output "ingress_configurator" {
  description = "Ingress configurator outputs, if bundled."
  value = var.deploy_ingress ? {
    app_name = one(juju_application.ingress_configurator[*].name)
    endpoints = {
      ingress       = "ingress"
      haproxy_route = "haproxy-route"
    }
  } : null
}
