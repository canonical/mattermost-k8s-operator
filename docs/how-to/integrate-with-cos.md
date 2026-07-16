---
myst:
    html_meta:
        "description lang=en": "Learn how to integrate the Mattermost charm with the Canonical Observability Stack (COS) for monitoring."
---

# Integrate with COS

## Integrate with Prometheus K8s operator

Deploy and integrate the [`prometheus-k8s`](https://charmhub.io/prometheus-k8s) charm with the `mattermost-k8s` charm through the `metrics-endpoint` relation via the `prometheus_scrape` interface. Prometheus should start scraping the metrics exposed at the `:8067/metrics` endpoint.

```
juju deploy prometheus-k8s
juju integrate mattermost-k8s prometheus-k8s
```

**Note**: Performance monitoring via the `/metrics` endpoint requires a Mattermost Entry, Enterprise, or Enterprise Advanced license. Without a valid license, Mattermost will not expose these metrics for Prometheus to scrape.

## Integrate with Loki K8s operator

Deploy and integrate the [`loki-k8s`](https://charmhub.io/loki-k8s) charm with the `mattermost-k8s` charm through
the `logging` relation via the `loki_push_api` interface. A Promtail worker will spawn and start pushing Mattermost server and application logs to Loki.

```
juju deploy loki-k8s
juju integrate mattermost-k8s loki-k8s
```

## Integrate with Grafana K8s operator

In order for the Grafana dashboards to function properly, Grafana must be able to connect to Prometheus and Loki as its data sources. Deploy and integrate the `prometheus-k8s` and `loki-k8s` charms with the [`grafana-k8s`](https://charmhub.io/grafana-k8s) charm through the `grafana-source` relation.

Note that the relation `grafana-source` has to be explicitly stated since `prometheus-k8s` and `grafana-k8s` share multiple interfaces.

```
juju deploy grafana-k8s
juju integrate prometheus-k8s:grafana-source grafana-k8s:grafana-source
juju integrate loki-k8s:grafana-source grafana-k8s:grafana-source
```

Then, the `mattermost-k8s` charm can be integrated with Grafana using the `grafana-dashboard` relation with the `grafana_dashboard` interface.

```
juju integrate mattermost-k8s grafana-k8s
```

To access the Grafana dashboard for the Mattermost charm, run the `get-admin-password` action to obtain credentials for admin access.

```
juju run grafana-k8s/0 get-admin-password
```

Log into the Grafana dashboard by visiting `http://<grafana-unit-ip>:3000`. Navigate to `http://<grafana-unit-ip>:3000/dashboards` and access the specific dashboard provided for Mattermost.