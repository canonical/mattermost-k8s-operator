# Mattermost charm

A juju charm deploying Mattermost, using a custom-built built image,
configurable to use a postgresql backend.

## Overview

This is a k8s workload charm and can only be deployed to to a Juju k8s
cloud, attached to a controller using `juju add-k8s`.

When visiting a fresh deployment, you will first be asked to create an admin
account.  Further accounts must be created using this admin account, or by
setting up an external authentication source, such as SAML.


## Details

See config option descriptions in config.yaml.

## Getting Started

Notes for deploying a test setup locally using microk8s:

    sudo snap install juju --classic
    sudo snap install juju-wait --classic
    sudo snap install microk8s --classic
    sudo snap alias microk8s.kubectl kubectl
    git clone https://git.launchpad.net/charm-k8s-mattermost
    git clone https://git.launchpad.net/~mattermost-charmers/charm-k8s-mattermost/+git/image-build mattermost-image-build

    microk8s.reset  # Warning! Clean slate!
    microk8s.enable dns dashboard registry storage
    microk8s.status --wait-ready
    microk8s.config | juju add-k8s myk8s --client

    # Build your Mattermost image
    docker build -t localhost:32000/mattermost ./mattermost-image-build
    docker push localhost:32000/mattermost
    
    juju bootstrap myk8s
    juju add-model mattermost-test
    juju deploy ./charm-k8s-mattermost --resource mattermost_image=localhost:32000/mattermost:latest mattermost
    juju wait
    juju status

The charm will not function without a database, so you will need to
deploy `cs:postgresql` somewhere.

If postgresql is deployed in the same model you plan to use for
mattermost, simply use `juju relate mattermost postgresql:db`.  (This
deployment style is recommended for testing purposes only.)

Cross-model relations are also supported.  Create a suitable model on
a different cloud, for example, LXD or OpenStack.

    juju switch database
    juju deploy cs:postgresql
    juju offer postgresql:db

In most k8s deployments, traffic to external services from worker pods
will be SNATed by some part of the infrastructure.  You will need to
know what the source addresses or address range is for the next step.

    juju switch mattermost-test
    juju find-offers  # note down offer URL; example used below:
    juju relate mattermost admin/database.postgresql --via 10.9.8.0/24

(In the case of postgresql, `--via` is needed so that the charm can
configure `pga_hba.conf` to let the k8s pods connect to the database.)
