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

  provisioner "local-exec" {
    command = "sleep 60; juju run ${self.name}/leader sync-s3-credentials access-key=${var.s3_integrator.access_key} secret-key=${var.s3_integrator.secret_key}"
  }
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

resource "juju_application" "ingress_configurator" {
  name       = "ingress-configurator"
  model_uuid = var.model_uuid

  charm {
    name     = "ingress-configurator"
    channel  = var.ingress_configurator.channel
    revision = var.ingress_configurator.revision
    base     = "ubuntu@24.04"
  }

  config = { hostname = var.external_hostname }
  trust  = true
  units  = 1
}

resource "juju_application" "self_signed_certificates" {
  name       = "self-signed-certificates"
  model_uuid = var.model_uuid

  charm {
    name     = "self-signed-certificates"
    channel  = var.self_signed_certificates.channel
    revision = var.self_signed_certificates.revision
  }

  units = 1
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

resource "juju_integration" "postgresql_tls" {
  model_uuid = var.model_uuid

  application {
    name     = juju_application.postgresql.name
    endpoint = "certificates"
  }

  application {
    name     = juju_application.self_signed_certificates.name
    endpoint = "certificates"
  }
}

resource "juju_integration" "mattermost_ingress" {
  model_uuid = var.model_uuid

  application {
    name     = module.mattermost.app_name
    endpoint = module.mattermost.requires.ingress
  }

  application {
    name     = juju_application.ingress_configurator.name
    endpoint = "ingress"
  }
}
