# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

provider "juju" {}

run "setup_tests" {
  module {
    source = "./tests/setup"
  }
}

run "basic_deploy" {
  command = plan

  variables {
    model_uuid        = run.setup_tests.model_uuid
    deploy_postgresql = true
    deploy_ingress    = false

    mattermost = {
      channel  = "latest/edge"
      revision = 54
    }

    postgresql = {
      channel  = "14/stable"
      revision = 960
    }

    s3_integrator = {
      channel    = "1/stable"
      revision   = 562
      access_key = "test-access-key"
      secret_key = "test-secret-key"
    }

    smtp_integrator = {
      channel  = "latest/stable"
      revision = 121
    }
  }

  assert {
    condition     = output.mattermost.app_name == "mattermost-k8s"
    error_message = "mattermost app_name did not match expected"
  }

  assert {
    condition     = length(juju_integration.mattermost_metrics) == 0
    error_message = "metrics-endpoint integration should be skipped when metrics_offer_url is null"
  }

  assert {
    condition     = length(juju_integration.mattermost_logging) == 0
    error_message = "logging integration should be skipped when logging_offer_url is null"
  }

  assert {
    condition     = length(juju_integration.mattermost_grafana_dashboard) == 0
    error_message = "grafana-dashboard integration should be skipped when grafana_dashboard_offer_url is null"
  }
}

run "cos_lite_integrated" {
  command = plan

  variables {
    model_uuid        = run.setup_tests.model_uuid
    deploy_postgresql = true
    deploy_ingress    = false

    mattermost = {
      channel  = "latest/edge"
      revision = 54
    }

    postgresql = {
      channel  = "14/stable"
      revision = 960
    }

    s3_integrator = {
      channel    = "1/stable"
      revision   = 562
      access_key = "test-access-key"
      secret_key = "test-secret-key"
    }

    smtp_integrator = {
      channel  = "latest/stable"
      revision = 121
    }

    metrics_offer_url           = "test-uuid@serviceaccount/test.prometheus-metrics-endpoint"
    logging_offer_url           = "test-uuid@serviceaccount/test.loki-logging"
    grafana_dashboard_offer_url = "test-uuid@serviceaccount/test.grafana-dashboards"
  }

  assert {
    condition     = output.mattermost.provides.metrics_endpoint == "metrics-endpoint"
    error_message = "metrics_endpoint provides endpoint did not match expected"
  }

  assert {
    condition     = output.mattermost.provides.grafana_dashboard == "grafana-dashboard"
    error_message = "grafana_dashboard provides endpoint did not match expected"
  }

  assert {
    condition     = output.mattermost.requires.logging == "logging"
    error_message = "logging requires endpoint did not match expected"
  }

  assert {
    condition     = length(juju_integration.mattermost_metrics) == 1
    error_message = "metrics-endpoint integration should be created when metrics_offer_url is set"
  }

  assert {
    condition     = length(juju_integration.mattermost_logging) == 1
    error_message = "logging integration should be created when logging_offer_url is set"
  }

  assert {
    condition     = length(juju_integration.mattermost_grafana_dashboard) == 1
    error_message = "grafana-dashboard integration should be created when grafana_dashboard_offer_url is set"
  }
}
