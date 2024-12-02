# Mattermost Operator

A Juju charm deploying and managing Mattermost on Kubernetes. [Mattermost](https://github.com/mattermost/mattermost)
is an open source platform for secure collaboration across the entire software
development lifecycle.

This charm simplifies initial deployment and “day N” operations of Mattermost
on Kubernetes, such as scaling the number of instances and clustering, access
to S3 and more. It allows for deployment on many different Kubernetes
platforms, from [MicroK8s](https://microk8s.io) to
[Charmed Kubernetes](https://ubuntu.com/kubernetes) to public cloud Kubernetes
offerings.

As such, the charm makes it easy for those looking to take control of their own
chat system whilst keeping operations simple, and gives them the freedom to
deploy on the Kubernetes platform of their choice.

For DevOps or SRE teams this charm will make operating Mattermost simple and
straightforward through Juju’s clean interface. It will allow easy deployment
into multiple environments for testing of changes, and supports scaling out for
enterprise deployments.

## Get started

To deploy the charm and relate it to
[the PostgreSQL K8s charm](https://charmhub.io/postgresql-k8s) within a Juju
Kubernetes model:

```
juju deploy postgresql-k8s
juju deploy mattermost-k8s
juju integrate mattermost-k8s postgresql-k8s:db
juju expose mattermost-k8s
```

Once the deployment has completed and the "mattermost-k8s" workload state in
`juju status` has changed to "active" you can visit `http://mattermost-k8s` in
a browser (assuming `mattermost-k8s` resolves to the IP(s) of your k8s ingress)
and log in to your Mattermost instance, and you'll be presented with a screen
to create an initial admin account.

Further accounts must be created using this
admin account, or by setting up an external authentication source, such as
SAML.

Refer to [Deploy the Mattermost charm for the first time](https://charmhub.io/mattermost-k8s/docs/tutorial-deploy-the-mattermost-charm-for-the-first-time) tutorial for more details.

### Basic operations

#### Add plugins and custom images
Refer to [How to add plugins and custom images](https://charmhub.io/mattermost-k8s/docs/add-plugins-custom-images)
for step-by-step instructions.

#### Authenticate
Refer to [How to authenticate](https://charmhub.io/mattermost-k8s/docs/authenticate)
for step-by-step instructions.

## Integrations

- [Postgresql](https://charmhub.io/postgresql-k8s) (required): PostgreSQL is a
powerful, open source object-relational database system. This is the default and
recommended database for all Mattermost installations.

Refer to [Integrations](https://charmhub.io/mattermost-k8s/) for a full list of
integrations.

## Learn more
* [Read more](https://charmhub.io/mattermost-k8s)
* [Developer documentation](https://developers.mattermost.com/)
* [Official webpage](https://github.com/mattermost/mattermost)
* [Troubleshooting](https://docs.mattermost.com/guides/deployment-troubleshooting.html)

## Project and community
* [Issues](https://github.com/canonical/mattermost-k8s-operator/issues)
* [Contributing](https://charmhub.io/mattermost-k8s/docs/contribute)
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
