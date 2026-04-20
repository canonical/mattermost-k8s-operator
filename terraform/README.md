<!-- Remember to update this file for your charm -- replace mattermost-k8s with the appropriate name. -->

# mattermost-k8s Terraform module

This folder contains a base [Terraform][Terraform] module for the mattermost-k8s charm.

The module uses the [Terraform Juju provider][Terraform Juju provider] to model the charm
deployment onto any Kubernetes environment managed by [Juju][Juju].

## Module structure

- **main.tf** - Defines the Juju application to be deployed.
- **variables.tf** - Allows customization of the deployment. Also models the charm configuration, 
  except for exposing the deployment options (Juju model name, channel or application name).
- **output.tf** - Integrates the module with other Terraform modules, primarily
  by defining potential integration endpoints (charm integrations), but also by exposing
  the Juju application name.
- **versions.tf** - Defines the Terraform provider version.

## Using mattermost-k8s base module in higher level modules

If you want to use `mattermost-k8s` base module as part of your Terraform module, import it
like shown below:

```text
data "juju_model" "my_model" {
  name = var.model
}

module "mattermost-k8s" {
  source = "git::https://github.com/canonical/mattermost-k8s-operator//terraform"
  
  model = juju_model.my_model.name
  # (Customize configuration variables here if needed)
}
```

Create integrations, for instance:

```text
resource "juju_integration" "mattermost-k8s-loki" {
  model = juju_model.my_model.name
  application {
    name     = module.mattermost-k8s.app_name
    endpoint = module.mattermost-k8s.endpoints.logging
  }
  application {
    name     = "loki-k8s"
    endpoint = "logging"
  }
}
```

The complete list of available integrations can be found [in the Integrations tab][mattermost-k8s-integrations].

[Terraform]: https://developer.hashicorp.com/terraform
[Terraform Juju provider]: https://registry.terraform.io/providers/juju/juju/latest
[Juju]: https://juju.is
[mattermost-k8s-integrations]: https://charmhub.io/mattermost-k8s/integrations
