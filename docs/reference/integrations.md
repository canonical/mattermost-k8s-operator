# Integrations

<!-- Use the template below to add information about integrations supported by this charm. -->

### `postgresql`

_Interface_: `postgresql_client`
_Supported charms_: [`postgresql-k8s`](https://charmhub.io/postgresql-k8s),
[PostgreSQL](https://charmhub.io/postgresql)

Database integration is a required relation for the Mattermost charm to supply
structured data storage for Mattermost.

Database integrate command: 
```
juju integrate mattermost-k8s postgresql-k8s
```
