---
myst:
  html_meta:
    "description lang=en": "Learn how to deploy, configure and operate the Mattermost K8s charm using Juju."
---

<!-- vale Canonical.007-Headings-sentence-case = NO -->

# Mattermost K8s charm

<!-- vale Canonical.007-Headings-sentence-case = YES -->

A [Juju](https://juju.is/) {ref}`charm <juju:charm>`
deploying and managing [Mattermost](https://mattermost.com/) on Kubernetes. Mattermost is a
flexible, open source messaging platform that enables secure team collaboration.

Like any Juju charm, this charm supports one-line deployment, configuration, integration, scaling,
and more. For the Mattermost K8s charm, this includes:

* High-availability clustering with Mattermost Enterprise Edition.
* S3-backed file storage and backups.
* Integration with the Canonical Observability Stack (COS).
* SMTP and `OAuth` integrations.

The Mattermost K8s charm allows for deployment on many different Kubernetes platforms, from
[MicroK8s](https://microk8s.io/) to [Charmed Kubernetes](https://ubuntu.com/kubernetes) to public
cloud Kubernetes offerings.

This charm will make operating Mattermost simple and straightforward for DevOps or SRE teams
through Juju's clean interface.

## In this documentation

```{list-table}
:header-rows: 1
:widths: 10 25

* -
  -
* - **Get started**
  - {ref}`Guided tutorial <deploy_the_mattermost_charm_for_the_first_time>` | {ref}`High-level deployment <reference_charm_architecture>`
* - **Deployment**
  - {ref}`Charm configuration <reference_configurations>`
* - **Operations**
  - {ref}`Backup and restore <how_to_back_up_restore>` | {ref}`Integrate with COS <how_to_integrate_with_cos>` | {ref}`Upgrade <how_to_upgrade>`
* - **Design**
  - {ref}`Architecture <reference_charm_architecture>`
* - **Security**
  - {ref}`Overview <explanation_security>`
```

## How this documentation is organized

This documentation uses the
[Diátaxis documentation structure](https://diataxis.fr/).

* The {ref}`Tutorial <deploy_the_mattermost_charm_for_the_first_time>` takes you step-by-step through a basic deployment of the Mattermost charm.
* The {ref}`How-to guides <how_to_index>` assume you have basic familiarity with the Mattermost charm. Learn more about setting up, using, maintaining, and contributing to this charm.
* {ref}`Reference <reference_index>` provides a guide to actions, configurations, relations, and other technical details.
* {ref}`Explanation <explanation_index>` holds discussion and clarification of key concepts behind the charm, such as security.
* {ref}`Release notes <release_notes_landing_page>` holds all the release notes for the charm, including any system or upgrade requirements.

## Contributing to this documentation

Documentation is an important part of this project, and we take the same open-source approach
to the documentation as the code. As such, we welcome community contributions, suggestions, and
constructive feedback on our documentation.
See {ref}`How to contribute <how_to_contribute>` for more information.

If there's a particular area of documentation that you'd like to see that's missing, please
[file a bug](https://github.com/canonical/mattermost-k8s-operator/issues).

## Project and community

The Mattermost K8s charm is a member of the Ubuntu family. It's an open-source project that warmly
welcomes community projects, contributions, suggestions, fixes, and constructive feedback.

- [Code of conduct](https://ubuntu.com/community/code-of-conduct)
- [Get support](https://discourse.charmhub.io/)
- [Join our online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
- {ref}`Contribute <how_to_contribute>`

Thinking about using the Mattermost K8s charm for your next project?
[Get in touch](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)!

```{toctree}
:hidden:
:maxdepth: 1

Tutorial <tutorial>
how-to/index
reference/index
explanation/index
release-notes/landing-page
```
