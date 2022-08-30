# Mattermost Operator

A Juju charm deploying and managing Mattermost on Kubernetes. Mattermost is an
open-source, self-hostable online chat service with file sharing, search, and
integrations.

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

## Usage

For details on using Kubernetes with Juju
[see here](https://juju.is/docs/kubernetes), and for details on using Juju with
MicroK8s for easy local testing
[see here](https://juju.is/docs/microk8s-cloud).

To deploy the charm and relate it to
[the PostgreSQL K8s charm](https://charmhub.io/postgresql-k8s) within a Juju
Kubernetes model:

```bash
juju deploy postgresql-k8s
juju deploy mattermost-k8s
juju relate mattermost-k8s postgresql-k8s:db
juju expose mattermost-k8s
```

Once the deployment has completed and the "mattermost-k8s" workload state in
`juju status` has changed to "active" you can visit `http://mattermost-k8s` in
a browser (assuming `mattermost-k8s` resolves to the IP(s) of your k8s ingress)
and log in to your Mattermost instance, and you'll be presented with a screen
to create an initial admin account. Further accounts must be created using this
admin account, or by setting up an external authentication source, such as
SAML.

For further details, [see here](https://charmhub.io/mattermost-k8s/docs).
