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

### `s3`

_Interface_: `s3`
_Supported_charms_: [`s3-integrator`](https://github.com/canonical/s3-integrator)

S3 integration allows Mattermost charm to store and retrieve files from an 
S3-compatible storage service, instead of using the local `./data` folder.
