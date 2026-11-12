---
myst:
  html_meta:
    "description lang=en": "Technical specifications for the Mattermost K8s charm's controls, integration interfaces, monitoring metrics, architecture, and releases."
---

(reference_index)=

# Reference

The Mattermost charm deploys Mattermost on Kubernetes and uses Juju to configure
it and connect it to PostgreSQL, S3, SMTP, and OAuth providers.

## Charm controls

The charm exposes configuration options and Juju actions to control application
behavior and perform administrative operations. These interfaces determine
which settings and operations are available to operators.

```{toctree}
:maxdepth: 1

actions
configurations
```

## Integrations and observability

Juju relations connect Mattermost to its database and optional services such as
object storage, email, and authentication. Application and runtime metrics
provide visibility into performance and help identify operational problems.

```{toctree}
:maxdepth: 1

integrations
metrics
```

## Architecture and releases

The charm uses a Kubernetes sidecar container and Pebble to manage the workload.

```{toctree}
:maxdepth: 1

charm-architecture
../changelog
```
