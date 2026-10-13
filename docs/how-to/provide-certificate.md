---
myst:
    html_meta:
        "description lang=en": "Learn how to enable TLS on PostgreSQL so it can be integrated with the Mattermost charm."
---

(how_to_provide_certificate)=

# How to provide a certificate

The `mattermost-k8s` charm requires TLS to be enabled on the PostgreSQL database it's
integrated with. To enable TLS, `postgresql-k8s` must be integrated with a charm that
provides certificates through the `certificates` relation.

## Use the self-signed-certificates charm

For development, testing, and other non-production environments, use the
[`self-signed-certificates`](https://charmhub.io/self-signed-certificates) charm. This
is the recommended and simplest way to satisfy the certificate requirement. The charm
creates its own certificate authority (CA), issues the requested certificates, and
renews them automatically.

Deploy the certificate provider:

```
juju deploy self-signed-certificates
```

Integrate it with `postgresql-k8s`:

```
juju integrate postgresql-k8s:certificates self-signed-certificates:certificates
```

When the certificate is available, both applications report an active status:

```{terminal}
juju status

App                        Status  Scale  Charm
postgresql-k8s              active      1  postgresql-k8s
self-signed-certificates    active      1  self-signed-certificates

Unit                          Workload  Agent  Message
postgresql-k8s/0*             active    idle   Primary
self-signed-certificates/0*   active    idle
```

Integrate `mattermost-k8s` with `postgresql-k8s` as usual.

```{caution}
Clients do not trust self-signed certificates by default. Do not use
`self-signed-certificates` in a production environment.
```

## Use a different certificate provider

For production deployments, use a certificate provider suited to your environment
instead of `self-signed-certificates`. See the
[X.509 certificates topic](https://charmhub.io/topics/security-with-x-509-certificates)
for an overview of the certificate provider charms available and guidance on choosing
one. 

Choose a certificate provider charm that implements the `tls-certificates` interface, and
integrate the charm with `postgresql-k8s` through its `certificates` endpoint.
