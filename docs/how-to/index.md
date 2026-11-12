---
myst:
  html_meta:
    "description lang=en": "Operate and maintain Mattermost on Kubernetes with database TLS, observability integrations, backups, and charm upgrades."
---

(how_to_index)=

# How-to guides

Manage the operational lifecycle of the Mattermost K8s charm, from integrating
supporting services to maintaining a production deployment. Each guide addresses
a specific task in a Juju-managed environment.

## Deployment integrations

Mattermost relies on a TLS-enabled PostgreSQL database for persistent data.
Integration with the Canonical Observability Stack (COS) adds metrics, logs, and
dashboards to help monitor the deployment.

```{toctree}
:maxdepth: 1

Provide a certificate <provide-certificate>
integrate-with-cos
```

## Maintenance and contribution

Database backups protect Mattermost's persistent data, while charm upgrades
bring new features and fixes to the deployment.

```{toctree}
:maxdepth: 1

back-up-restore
upgrade
contribute
```
