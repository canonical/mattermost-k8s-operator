---
myst:
  html_meta:
    "description lang=en": "Task-oriented guides for the Mattermost charm: database TLS, COS integration, push notifications, backups, upgrades, and contributing."
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
Integrate with COS <integrate-with-cos>
```

## Configuration

Charm configuration options control Mattermost features, such as push notifications
to the Mattermost mobile apps.

```{toctree}
:maxdepth: 1

Manage push notifications <manage-push-notifications>
```

## Maintenance and contribution

Backups protect Mattermost's persistent data, and upgrades bring new features and
fixes.

```{toctree}
:maxdepth: 1

Back up and restore <back-up-restore>
Upgrade <upgrade>
Contribute <contribute>
```
