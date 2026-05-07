# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

module "mattermost" {
  source     = "../"
  model_uuid = var.model_uuid
  app_name   = var.mattermost.app_name
  channel    = var.mattermost.channel
  revision   = var.mattermost.revision
  base       = var.mattermost.base
  config     = var.mattermost.config
  units      = var.mattermost.units
}

resource "juju_application" "postgresql" {
  name       = "postgresql-k8s"
  model_uuid = var.model_uuid

  charm {
    name     = "postgresql-k8s"
    channel  = var.postgresql.channel
    revision = var.postgresql.revision
  }

  config = var.postgresql.config
  trust  = true
  units  = var.postgresql.units
}

resource "juju_application" "s3_integrator" {
  name       = "s3-integrator"
  model_uuid = var.model_uuid

  charm {
    name     = "s3-integrator"
    channel  = var.s3_integrator.channel
    revision = var.s3_integrator.revision
  }

  config = var.s3_integrator.config
  units  = 1
}

resource "juju_application" "smtp_integrator" {
  name       = "smtp-integrator"
  model_uuid = var.model_uuid

  charm {
    name     = "smtp-integrator"
    channel  = var.smtp_integrator.channel
    revision = var.smtp_integrator.revision
  }

  config = var.smtp_integrator.config
  units  = 1
}

module "ingress_configurator" {
  source     = "git::https://github.com/canonical/ingress-configurator-operator//terraform?ref=rev72&depth=1"
  app_name   = "ingress-configurator"
  model_uuid = var.model_uuid
  channel    = var.ingress_configurator.channel
  revision   = var.ingress_configurator.revision
  config     = { hostname = var.external_hostname }
}

# --- Integrations ---

resource "juju_integration" "mattermost_postgresql" {
  model_uuid = var.model_uuid

  application {
    name     = module.mattermost.app_name
    endpoint = module.mattermost.requires.postgresql
  }

  application {
    name     = juju_application.postgresql.name
    endpoint = "database"
  }
}

resource "juju_integration" "mattermost_s3" {
  model_uuid = var.model_uuid

  application {
    name     = module.mattermost.app_name
    endpoint = module.mattermost.requires.s3
  }

  application {
    name     = juju_application.s3_integrator.name
    endpoint = "s3-credentials"
  }
}

resource "juju_integration" "mattermost_smtp" {
  model_uuid = var.model_uuid

  application {
    name     = module.mattermost.app_name
    endpoint = module.mattermost.requires.smtp
  }

  application {
    name     = juju_application.smtp_integrator.name
    endpoint = "smtp"
  }
}

resource "juju_integration" "mattermost_ingress" {
  model_uuid = var.model_uuid

  application {
    name     = module.mattermost.app_name
    endpoint = module.mattermost.requires.ingress
  }

  application {
    name     = module.ingress_configurator.app_name
    endpoint = module.ingress_configurator.endpoints.ingress
  }
}
