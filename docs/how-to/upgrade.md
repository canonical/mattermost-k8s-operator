---
myst:
  html_meta:
    "description lang=en": "Learn how to upgrade the Mattermost charm to a new revision."
---

(how_to_upgrade)=

# How to upgrade

The Mattermost charm is a stateless Kubernetes charm. To upgrade the Mattermost
charm to the latest version, simply run the `juju refresh` command, for example:

```bash
juju refresh mattermost-k8s
```
