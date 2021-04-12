# Mattermost Operator

A Juju charm deploying and managing Mattermost on Kubernetes, configurable to use a PostgreSQL backend.

## Overview

Mattermost offers both [a Team Edition and an Enterprise Edition](https://mattermost.com/pricing-feature-comparison/).
This charm supports both, with the default image deploying the Team Edition. Supported
features include authentication via SAML, Push Notifications, clustering,
the storage of images and attachments in S3, and a Prometheus exporter for
performance monitoring. This charm also offers seamless Mattermost version
upgrades, initiated by switching to an image with a newer version of
Mattermost than the one currently deployed.

## Usage

For details on using Kubernetes with Juju [see here](https://juju.is/docs/kubernetes), and for
details on using Juju with MicroK8s for easy local testing [see here](https://juju.is/docs/microk8s-cloud).

To deploy the charm and relate it to [the PostgreSQL K8s charm](https://charmhub.io/postgresql-k8s) within a Juju
Kubernetes model:

    juju deploy cs:~postgresql-charmers/postgresql-k8s postgresql
    juju deploy cs:~mattermost-charmers/mattermost --config juju-external-hostname=foo.internal
    juju relate mattermost postgresql:db
    juju expose mattermost

Once the deployment has completed and the "mattermost" workload state in `juju
status` has changed to "active" you can visit http://${mattermost_ip}:8065 in a browser and log in to
your Mattermost instance, and you'll be presented with a screen to create an
initial admin account. Further accounts must be created using this admin account, or by
setting up an external authentication source, such as SAML.

For further details, [see here](https://charmhub.io/mattermost-charmers-mattermost/docs).
