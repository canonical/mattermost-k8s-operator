# Charm deployment and architecture

Add overview material here:

1. What kind of application is it? What kind of software does it use?
2. Describe Pebble services.

<!-- Example text
At its core, the __charm_name__ charm is <software> that does <brief description>.

The charm design leverages the [sidecar](https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/#example-1-sidecar-containers) pattern to allow multiple containers in each pod with [Pebble](https://documentation.ubuntu.com/juju/3.6/reference/pebble/) running as the workload container’s entrypoint.

Pebble is a lightweight, API-driven process supervisor that is responsible for configuring processes to run in a container and controlling those processes throughout the workload lifecycle.

Pebble `services` are configured through [layers](https://github.com/canonical/pebble#layer-specification), and the following containers represent each one a layer forming the effective Pebble configuration, or `plan`:

1. Container 1, which does this and that.
2. Container 2, which does that and this.
3. And so on.


As a result, if you run a `kubectl get pods` on a namespace named for the Juju model you've deployed the __charm_name__ charm into, you'll see something like the following:

```bash
NAME                             READY   STATUS    RESTARTS   AGE
__charm_name__-0                   N/N     Running   0         6h4m
```

This shows there are <NUMBER> containers - <describe what the containers are>.
-->

## High-level overview of __charm_name__ deployment

The following diagram shows a typical deployment of the __charm_name__ charm.
<!-- 
    Provide a brief description of the deployment here. Is it a Kubernetes cloud, a VM, or both?
    What other charms are included in this deployment? 
-->

<!-- Include a Mermaid diagram of the charm deployment here. 
     Use one container per charm; the point of this high-level overview is to show
     a typical deployment and not provide a detailed breakdown of any of the charms.
     Provide a brief description of the relations (for instance, "provides connection",
     "caches storage", or "provides database"). More information on how to create mermaid diagrams
     can be found in https://canonical-platform-engineering.readthedocs-hosted.com/en/latest/engineering-practices/documentation/architecture-diagram-guidance/
-->

## Charm architecture

<!-- Include a Mermaid diagram of the charm here. Include here if the diagram is not included in explanation/charm-architecture.md
     Limit the scope of this diagram to the charm only.
     How is the charm containerized? Include those separate pieces in this diagram.
-->

### Containers

Configuration files for the containers can be found in the respective directories that define the rock.

<!--
#### Container example

Description of container.

The workload that this container is running is defined in the [<container-name> rock](link to rock).
-->

## OCI images

We use [Rockcraft](https://canonical-rockcraft.readthedocs-hosted.com/en/latest/) to build OCI Images for __charm_name__.
The images are defined in [__charm_name__ rock](link to rock).
They are published to [Charmhub](https://charmhub.io/), the official repository of charms.

> See more: [How to publish your charm on Charmhub](https://canonical-charmcraft.readthedocs-hosted.com/en/stable/howto/manage-charms/#publish-a-charm-on-charmhub)

## Metrics

<!--
If the charm uses metrics, include a list under reference/metrics.md and link that document here.
If the charm uses containers, you may include text here like:

Inside the above mentioned containers, additional Pebble layers are defined in order to provide metrics.
See [metrics](link-to-metrics-document) for more information.
-->

## Juju events

For this charm, the following Juju events are observed:

<!--
Numbered list of Juju events. Link to describe the event in more detail (either in Juju docs or in a specific charm's docs). When is the event fired? What does the event indicate/mean?
-->

> See more in the Juju docs: [Hook](https://documentation.ubuntu.com/juju/latest/user/reference/hook/)

## Charm code overview

The `src/charm.py` is the default entry point for a charm and has the <relevant-charm-class> Python class which inherits
from CharmBase. CharmBase is the base class from which all charms are formed, defined
by [Ops](https://ops.readthedocs.io/en/latest/index.html) (Python framework for developing charms).

> See more in the Juju docs: [Charm](https://documentation.ubuntu.com/juju/latest/user/reference/charm/)

The `__init__` method guarantees that the charm observes all events relevant to its operation and handles them.

Take, for example, when a configuration is changed by using the CLI.

1. User runs the configuration command:

```bash
juju config <relevant-charm-configuration>
```

2. A `config-changed` event is emitted.
3. In the `__init__` method is defined how to handle this event like this:

```python
self.framework.observe(self.on.config_changed, self._on_config_changed)
```

4. The method `_on_config_changed`, for its turn, will take the necessary actions such as waiting for all the relations to be ready and then configuring the containers.
