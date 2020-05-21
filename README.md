# Mattermost charm

A juju charm deploying Mattermost, using a custom-built built image,
configurable to use a postgresql backend.

## Overview

This is a k8s charm and can only be deployed to to a Juju k8s cloud,
attached to a controller using `juju add-k8s`.

Configuration for the Mattermost image is in standard Juju config. In
particular:

* `pg_db_host`, `pg_db_port`, `pg_user`, `pg_password`: this charm should be
  able in the future, to relate to postgresql, but as of now these parameters
  allow setting up the connection.

On a fresh deployment, you need to set Mattermost in Open Server mode, which will let you create an admin account.
Once this is done, you can restrict access with:

```
juju config mattermost open_server=false
```

## Details

See config option descriptions in config.yaml.

## Quickstart

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
    juju config mattermost pg_db_host=10.1.1.1 pg_password=secret
    juju wait
    juju status
