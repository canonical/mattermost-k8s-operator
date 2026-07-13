# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variable "model_uuid" {
  description = "UUID of the Juju model where the applications will be deployed."
  type        = string
}

variable "external_hostname" {
  description = "External hostname for ingress (used by ingress-configurator)."
  type        = string
  default     = ""
}

variable "deploy_postgresql" {
  description = "Whether to deploy the bundled postgresql-k8s charm (with self-signed TLS). Set to false to integrate an external PostgreSQL via an offer instead."
  type        = bool
  default     = true
}

variable "deploy_ingress" {
  description = "Whether to deploy the bundled ingress-configurator charm. Set to false to manage ingress externally."
  type        = bool
  default     = true
}

variable "mattermost" {
  description = "Mattermost charm configuration."
  type = object({
    app_name = optional(string, "mattermost-k8s")
    channel  = string
    revision = number
    base     = optional(string, "ubuntu@24.04")
    config   = optional(map(string), {})
    units    = optional(number, 1)
  })
}

variable "postgresql" {
  description = "PostgreSQL K8s charm configuration."
  type = object({
    channel  = string
    revision = number
    config   = optional(map(string), {})
    units    = optional(number, 1)
  })
}

variable "s3_integrator" {
  description = "S3 integrator charm configuration."
  type = object({
    channel    = string
    revision   = number
    config     = optional(map(string), {})
    access_key = string
    secret_key = string
  })
}

variable "smtp_integrator" {
  description = "SMTP integrator charm configuration."
  type = object({
    channel  = string
    revision = number
    config   = optional(map(string), {})
  })
}

variable "smtp_password" {
  description = "SMTP AUTH password. When set, it is stored as a Juju secret and referenced by smtp-integrator via password_secret."
  type        = string
  sensitive   = true
  default     = ""
}

variable "oauth" {
  description = "OAuth external IdP integrator charm configuration."
  type = object({
    channel  = optional(string, "edge")
    revision = optional(number, null)
    base     = optional(string, "ubuntu@22.04")
    config   = optional(map(string), {})
  })
  default = {}
}

variable "self_signed_certificates" {
  description = "Self-signed certificates charm configuration."
  type = object({
    channel  = optional(string, "latest/stable")
    revision = optional(number, null)
  })
  default = {}
}

variable "ingress_configurator" {
  description = "Ingress configurator charm configuration."
  type = object({
    channel  = optional(string, "latest/edge")
    revision = optional(number, 72)
  })
  default = {}
}
