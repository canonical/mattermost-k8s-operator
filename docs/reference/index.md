---
myst:
  html_meta:
    "description lang=en": "Technical specifications for the Mattermost K8s charm's controls, integration interfaces, monitoring metrics, architecture, and releases."
---

(reference_index)=

# Reference

Technical specifications and architectural details describe the Mattermost K8s
charm's configuration, interfaces, and runtime behavior. They provide a basis for
operating the charm and integrating it with other services.

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

Kubernetes sidecar containers and Pebble underpin the charm's workload management
and its interactions with supporting services. The architecture provides context
for runtime behavior, while the release history tracks changes to supported
capabilities.

```{toctree}
:maxdepth: 1

charm-architecture
../changelog
```
