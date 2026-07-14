Charm architecture
==================

At its core, `Mattermost <https://mattermost.com/>`__ is a Go application that provides a self-hosted messaging platform for secure team collaboration. It integrates with `PostgreSQL <https://www.postgresql.org/>`__ as its database and optionally with `S3 <https://aws.amazon.com/s3/>`__-compatible storage for file management.

The charm design leverages the `sidecar <https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/#example-1-sidecar-containers>`__ pattern to allow multiple containers in each pod with `Pebble <https://documentation.ubuntu.com/pebble/>`__ running as the workload container's entrypoint.

Pebble is a lightweight, API-driven process supervisor that is responsible for configuring processes to run in a container and controlling those processes throughout the workload lifecycle.

Pebble ``services`` are configured through `layers <https://github.com/canonical/pebble#layer-specification>`__, and the following container represents a layer forming the effective Pebble configuration, or ``plan``:

1. A `Mattermost <https://mattermost.com/>`__ container, which runs the Mattermost server application via a startup script that translates charm integration data into Mattermost environment variables.

As a result, if you run ``kubectl get pods`` on a namespace named for the Juju model you've deployed the Mattermost charm into, you'll see something like the following:

.. code:: bash

   NAME                             READY   STATUS    RESTARTS   AGE
   mattermost-k8s-0                 2/2     Running   0          6h4m

This shows there are two containers - the one named above, as well as a container for the charm code itself.

And if you run ``kubectl describe pod mattermost-k8s-0``, all the containers will have as Command ``/charm/bin/pebble``. That's because Pebble is responsible for the processes startup as explained above.

Below is a diagram of the application architecture of Mattermost. Mattermost is the main application container, which is configured and managed by the charm logic running in a separate container. The charm logic uses Pebble to interact with the Mattermost process and ensure it is running with the correct configuration, renaming the environment variables to work with Mattermost using ``start.sh``.

.. mermaid::

   C4Container
     System_Boundary(sb_mattermost, "Mattermost Charm") {
       Container_Boundary(cb_app, "App Container") {
         Component(comp_server, "Mattermost Server", "Go Application", "Serves the messaging platform on port 8080")
         Component(comp_start, "start.sh", "Bash Script", "Maps integration data to Mattermost environment variables")
       }
       Container_Boundary(cb_charm, "Charm Container") {
         Component(comp_logic, "Charm Logic", "paas-charm Go Framework", "Controls application deployment & config")
       }
     }
     Rel(comp_logic, comp_server, "Supervises process via Pebble")
     Rel(comp_start, comp_server, "Configures & launches")
     UpdateRelStyle(comp_logic, comp_server, $offsetY="10", $offsetX="-60")
     UpdateRelStyle(comp_start, comp_server, $offsetX="20")

High-level overview of a Mattermost deployment
----------------------------------------------

The following diagram shows a typical deployment of the Mattermost charm on a Kubernetes cloud. It consists of the Mattermost charm and a required PostgreSQL charm, with optional integrations for S3 storage, SMTP email, ``OAuth`` authentication, and ingress. The resulting deployment is a fully functional Mattermost instance that is secure with authentication, has persistent cloud storage, and is accessible from outside the cluster. 

.. mermaid::

   C4Container
   title System Architecture: Mattermost Deployment

   Container_Boundary(mattermost_boundary, "Mattermost") {
     System(mattermost, "Mattermost Charm", "Handles team communication and collaboration.")
   }

   System_Boundary(postgres_boundary, "PostgreSQL") {
     SystemDb(postgres, "PostgreSQL", "Required database for storing persistent data.")
   }

   System_Boundary(s3_boundary, "S3 Integrator") {
     SystemDb(s3, "S3 Integrator", "Optional file storage for attachments.")
   }

   System_Boundary(smtp_boundary, "SMTP Integrator") {
     System(smtp, "SMTP Integrator", "Optional email relay service.")
   }

   Person(user, "User", "End user connecting to the Mattermost instance.")

   Rel(user, mattermost, "connects to")
   BiRel(mattermost, postgres, "stores data")
   BiRel(mattermost, s3, "stores files")
   BiRel(mattermost, smtp, "sends email")
   
   UpdateRelStyle(user, mattermost, $offsetY="-20")
   UpdateRelStyle(mattermost, s3, $offsetX="10")
   UpdateRelStyle(mattermost, postgres, $offsetX="-20", $offsetY="10")

Mattermost container
----------

Mattermost is a Go application started via a ``start.sh`` script that maps environment variables provided by the charm integrations (PostgreSQL, S3, SMTP, ``OAuth``) into Mattermost's native ``MM_*`` configuration format.

The Mattermost server listens on port ``8080`` and serves the messaging platform, including its web client, REST API, and WebSocket connections.

The container also includes a set of third-party plugins:

-  |Autolink|_
-  |Matterpoll|_
-  |Giphy|_
-  |Remind|_

.. |Autolink| replace:: :code:`Autolink`
.. _Autolink: https://github.com/mattermost-community/mattermost-plugin-autolink
.. |Matterpoll| replace:: :code:`Matterpoll`
.. _Matterpoll: https://github.com/matterpoll/matterpoll
.. |Giphy| replace:: :code:`Giphy`
.. _Giphy: https://github.com/moussetc/mattermost-plugin-giphy
.. |Remind| replace:: :code:`Remind`
.. _Remind: https://github.com/scottleedavis/mattermost-plugin-remind

The workload that this container is running is defined in the `Mattermost rock <https://github.com/canonical/mattermost-k8s-operator/tree/main/mattermost_rock>`__.

OCI images
----------

We use `Rockcraft <https://canonical-rockcraft.readthedocs-hosted.com/en/latest/>`__ to build the OCI image for Mattermost. The image is defined in the `Mattermost rock <https://github.com/canonical/mattermost-k8s-operator/tree/main/mattermost_rock>`__ and is published to `Charmhub <https://charmhub.io/>`__, the official repository of charms. This is done by publishing a resource to Charmhub as described in the `Charmcraft how-to guides <https://canonical-charmcraft.readthedocs-hosted.com/en/stable/howto/manage-charms/#publish-a-charm-on-charmhub>`__.

Integrations
------------

PostgreSQL
~~~~~~~~~~

PostgreSQL is an open-source object-relational database used by Mattermost to store all persistent data, including users, teams, channels and messages. This is a required integration, the charm will remain in a blocked state until PostgreSQL is integrated.

S3
~~

S3-compatible object storage allows Mattermost to store and retrieve uploaded files (attachments, images, and other media) externally rather than using local filesystem storage. This is an optional integration.

SMTP
~~~~

SMTP enables Mattermost to send outgoing email notifications such as password resets, team invitations, and message alerts through an external SMTP relay. This is an optional integration.

``OAuth``
~~~~~~~~~

The ``OAuth`` integration via `Hydra <https://charmhub.io/hydra>`__ enables OpenID Connect-based single sign-on (SSO), allowing users to authenticate through an external identity provider. This is an optional integration.

Ingress
~~~~~~~

The Mattermost charm supports integration with `Ingress <https://kubernetes.io/docs/concepts/services-networking/ingress/#what-is-ingress>`__, provided automatically by the ``go-framework`` extension. This allows external traffic to be routed to the Mattermost workload.

Observability
~~~~~~~~~~~~~

The Mattermost charm supports integration with the `Canonical Observability Stack (COS) <https://charmhub.io/topics/canonical-observability-stack>`__:

-  **Prometheus**: metrics are exposed and can be scraped by the `Prometheus operator <https://charmhub.io/prometheus-k8s>`__ via the ``metrics-endpoint`` integration.
-  **Grafana**: dashboards can be provided to the `Grafana operator <https://charmhub.io/grafana-k8s>`__ via the ``grafana-dashboard`` integration.
-  **Loki**: logs can be pushed to the `Loki operator <https://charmhub.io/loki-k8s>`__ via the ``logging`` integration.

Juju events
-----------

For this charm, the following events are observed:

1. |pebble_ready|_: fired on Kubernetes charms when the requested container is ready. Action: check that all required integrations are present and configure the Mattermost container.
2. |config_changed|_: usually fired in response to a configuration change using the CLI. Action: validate the configuration and restart the workload.
3. |update_status|_: periodic event. Action: reconcile the workload state and refresh ingress data.
4. Integration events for ``postgresql``, ``s3``, ``smtp``, and ``oauth``: fired when integration data changes. Action: update the workload configuration and restart the service.
5. |grant_admin_role_action|_: fired when the ``grant-admin-role`` action is executed. Action: Grant the ``system_admin`` role to a user.

.. |pebble_ready| replace:: :code:`pebble_ready`
.. _pebble_ready: https://documentation.ubuntu.com/juju/latest/user/reference/hook/#container-pebble-ready
.. |config_changed| replace:: :code:`config_changed`
.. _config_changed: https://documentation.ubuntu.com/juju/latest/user/reference/hook/#config-changed
.. |update_status| replace:: :code:`update_status`
.. _update_status: https://documentation.ubuntu.com/juju/latest/user/reference/hook/#update-status
.. |grant_admin_role_action| replace:: :code:`grant_admin_role_action`
.. _grant_admin_role_action: https://charmhub.io/mattermost-k8s/actions

..

   See more in the Juju docs: `Hook <https://documentation.ubuntu.com/juju/latest/user/reference/hook/>`__

Charm code overview
-------------------

The ``src/charm.py`` is the default entry point for a charm and has the ``MattermostK8sCharm`` Python class which inherits from ``paas_charm.go.Charm``.

``paas_charm.go.Charm`` is a base class provided by the `paas-charm <https://github.com/canonical/paas-charm>`__ library, which extends `Ops <https://documentation.ubuntu.com/ops/latest/>`__ (Python framework for developing charms) with built-in support for Go workloads, Pebble service management, and standard integrations (PostgreSQL, S3, ingress, observability).

The charm itself is minimal, the ``go-framework`` `Charmcraft extension <https://documentation.ubuntu.com/charmcraft/stable/reference/extensions/>`__ provides the majority of the operational logic, including Pebble layer management, integration handling, and status reporting. Workload-specific configuration is handled by the ``start.sh`` script inside the rock, which converts environment variables set by the charm framework into Mattermost's native ``MM_*`` environment variable format.

See more information in `Charm <https://documentation.ubuntu.com/juju/latest/user/reference/charm/>`__.