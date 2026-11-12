---
myst:
  html_meta:
    "description lang=en": "Task-oriented guides for the Mattermost charm: database TLS, COS integration, backups, upgrades, and contributing."
---

(how_to_index)=

# How-to guides

Run and maintain Mattermost on Kubernetes with Juju. These tasks assume the
charm is already deployed.

## Deployment integrations

Mattermost requires a PostgreSQL database with TLS enabled, and can send metrics,
logs, and dashboards to the Canonical Observability Stack (COS) to help monitor the deployment.

```{toctree}
:maxdepth: 1

Provide a certificate <provide-certificate>
integrate-with-cos
```

## Maintenance and contribution

Backups protect Mattermost's persistent data, and upgrades bring new features and
fixes.

```{toctree}
:maxdepth: 1

back-up-restore
upgrade
contribute
```
