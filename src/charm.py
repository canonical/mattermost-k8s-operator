#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import subprocess  # nosec
from ipaddress import ip_network
from urllib.parse import urlparse
from zlib import crc32

import ops.lib
from ops.charm import CharmBase, CharmEvents
from ops.framework import EventBase, EventSource, StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus

import environment
from utils import extend_list_merging_dicts_matched_by_key

pgsql = ops.lib.use("pgsql", 1, "postgresql-charmers@lists.launchpad.net")

logger = logging.getLogger()


# Mattermost's default port, and what we expect the image to use
CONTAINER_PORT = 8065
# Default port, enforced via envConfig to prevent operator error
METRICS_PORT = 8067
DATABASE_NAME = "mattermost"
LICENSE_SECRET_KEY_NAME = "licence"  # nosec
REQUIRED_S3_SETTINGS = ["s3_bucket", "s3_region", "s3_access_key_id", "s3_secret_access_key"]
REQUIRED_SETTINGS = ["mattermost_image_path"]
REQUIRED_SSO_SETTINGS = ["licence", "site_url"]
SAML_IDP_CRT = "saml-idp.crt"


class MattermostDBMasterAvailableEvent(EventBase):
    pass


class MattermostCharmEvents(CharmEvents):
    """Custom charm events."""

    db_master_available = EventSource(MattermostDBMasterAvailableEvent)


def check_ranges(ranges, name):
    """If ranges has one or more invalid elements, return a string describing the problem.

    ranges is a string containing a comma-separated list of CIDRs, a CIDR being the only kind of valid element.
    """
    networks = ranges.split(",")
    invalid_networks = []
    for network in networks:
        try:
            ip_network(network)
        except ValueError:
            invalid_networks.append(network)
    if invalid_networks:
        return "{}: invalid network(s): {}".format(name, ", ".join(invalid_networks))


def get_container(pod_spec, container_name):
    """Find and return the first container in pod_spec whose name is container_name, otherwise return None."""
    for container in pod_spec["containers"]:
        if container["name"] == container_name:
            return container
    raise ValueError("Unable to find container named '{}' in pod spec".format(container_name))


def get_env_config(pod_spec, container_name):
    """Return the envConfig of the container in pod_spec whose name is container_name, otherwise return None.

    If the container exists but has no envConfig, raise KeyError.
    """
    container = get_container(pod_spec, container_name)
    if "envConfig" in container:
        return container["envConfig"]
    else:
        raise ValueError(
            "Unable to find envConfig for container named '{}'".format(container_name)
        )


class MattermostK8sCharm(CharmBase):
    state = StoredState()
    on = MattermostCharmEvents()

    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(self.on.start, self.configure_pod)
        self.framework.observe(self.on.config_changed, self.configure_pod)
        self.framework.observe(self.on.leader_elected, self.configure_pod)
        self.framework.observe(self.on.upgrade_charm, self.configure_pod)

        # actions
        self.framework.observe(self.on.grant_admin_role_action, self._on_grant_admin_role_action)

        # database
        self.state.set_default(db_conn_str=None, db_uri=None, db_ro_uris=[])
        self.db = pgsql.PostgreSQLClient(self, "db")
        self.framework.observe(
            self.db.on.database_relation_joined, self._on_database_relation_joined
        )
        self.framework.observe(self.db.on.master_changed, self._on_master_changed)
        self.framework.observe(self.db.on.standby_changed, self._on_standby_changed)
        self.framework.observe(self.on.db_master_available, self.configure_pod)

    def _on_grant_admin_role_action(self, event):
        """Handle the grant-admin-role action."""
        user = event.params["user"]
        cmd = ["/mattermost/bin/mattermost", "roles", "system_admin", user]
        granted = subprocess.run(cmd, capture_output=True)  # nosec
        if granted.returncode != 0:
            event.fail(
                "Failed to run '{}'. Output was:\n{}".format(
                    " ".join(cmd), granted.stderr.decode("utf-8")
                )
            )
        else:
            msg = (
                "Ran grant-admin-role for user '{}'. They will need to log out and log back in "
                "to Mattermost to fully receive their permissions upgrade.".format(user)
            )
            event.set_results({"info": msg})

    @property
    def _site_url(self):
        """Return our site URL, defaulting to the deployed juju application name."""
        return self.config["site_url"] or "http://{}".format(self.app.name)

    def _on_database_relation_joined(self, event: pgsql.DatabaseRelationJoinedEvent):
        """Handle db-relation-joined."""
        if self.model.unit.is_leader():
            # Provide requirements to the PostgreSQL server.
            event.database = DATABASE_NAME  # Request database named mydbname
            # event.extensions = ['citext']  # Request the citext extension installed
        elif event.database != DATABASE_NAME:
            # Leader has not yet set requirements. Defer, in case this unit
            # becomes leader and needs to perform that operation.
            event.defer()
            return

    def _on_master_changed(self, event: pgsql.MasterChangedEvent):
        """Handle changes in the primary database unit."""
        if event.database != DATABASE_NAME:
            # Leader has not yet set requirements. Wait until next
            # event, or risk connecting to an incorrect database.
            return

        self.state.db_conn_str = None if event.master is None else event.master.conn_str
        self.state.db_uri = None if event.master is None else event.master.uri

        if event.master is None:
            return

        self.on.db_master_available.emit()

    def _on_standby_changed(self, event: pgsql.StandbyChangedEvent):
        """Handle changes in the secondary database unit(s)."""
        if event.database != DATABASE_NAME:
            # Leader has not yet set requirements. Wait until next
            # event, or risk connecting to an incorrect database.
            return

        self.state.db_ro_uris = [c.uri for c in event.standbys]

        # TODO(pjdc): Emit event when we add support for read replicas.

    def _check_for_config_problems(self):
        """Check for simple configuration problems and return a string describing them, otherwise an empty string."""
        problems = []

        missing = sorted(environment.missing_config_settings(self.config))
        if missing:
            problems.append("required setting(s) empty: {}".format(", ".join(missing)))

        ranges = self.model.config["ingress_whitelist_source_range"]
        if ranges:
            problems.append(check_ranges(ranges, "ingress_whitelist_source_range"))

        return "; ".join(filter(None, problems))

    def _make_pod_spec(self):
        """Return a pod spec with some core configuration."""
        pod_config = environment.generate(
            self.model.config, self.app.name, self._site_url, self.state.db_uri
        )

        mattermost_image_details = {
            "imagePath": self.model.config["mattermost_image_path"],
        }
        if self.model.config["mattermost_image_username"]:
            mattermost_image_details.update(
                {
                    "username": self.model.config["mattermost_image_username"],
                    "password": self.model.config["mattermost_image_password"],
                }
            )

        return {
            "version": 3,  # otherwise resources are ignored
            "containers": [
                {
                    "name": self.app.name,
                    "imageDetails": mattermost_image_details,
                    "ports": [{"containerPort": CONTAINER_PORT, "protocol": "TCP"}],
                    "envConfig": pod_config,
                    "kubernetes": {
                        "readinessProbe": {
                            "httpGet": {"path": "/api/v4/system/ping", "port": CONTAINER_PORT}
                        },
                    },
                }
            ],
        }

    def _update_pod_spec_for_k8s_ingress(self, pod_spec):
        """Add resources to pod_spec configuring site ingress, if needed."""
        parsed = urlparse(self._site_url)

        if not parsed.scheme.startswith("http"):
            return

        annotations = {
            "nginx.ingress.kubernetes.io/proxy-body-size": "{}m".format(
                self.model.config["max_file_size"]
            )
        }
        ingress = {
            "name": "{}-ingress".format(self.app.name),
            "spec": {
                "rules": [
                    {
                        "host": parsed.hostname,
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "backend": {
                                        "serviceName": self.app.name,
                                        "servicePort": CONTAINER_PORT,
                                    },
                                }
                            ]
                        },
                    }
                ]
            },
        }
        if parsed.scheme == "https":
            ingress["spec"]["tls"] = [{"hosts": [parsed.hostname]}]
            tls_secret_name = self.model.config["tls_secret_name"]
            if tls_secret_name:
                ingress["spec"]["tls"][0]["secretName"] = tls_secret_name
        else:
            annotations["nginx.ingress.kubernetes.io/ssl-redirect"] = "false"

        ingress_whitelist_source_range = self.model.config["ingress_whitelist_source_range"]
        if ingress_whitelist_source_range:
            annotations[
                "nginx.ingress.kubernetes.io/whitelist-source-range"
            ] = ingress_whitelist_source_range

        ingress["annotations"] = annotations

        # Due to https://github.com/canonical/operator/issues/293 we
        # can't use pod.set_spec's k8s_resources argument.
        resources = pod_spec.get("kubernetesResources", {})
        resources["ingressResources"] = [ingress]
        pod_spec["kubernetesResources"] = resources

    def _get_licence_secret_name(self):
        """Compute a content-dependent name for the licence secret.

        The name is varied so that licence updates cause the pods to
        be respawned.  Mattermost reads the licence file on startup
        and updates the copy in the database, if necessary.
        """
        crc = "{:08x}".format(crc32(self.model.config["licence"].encode("utf-8")))
        return "{}-licence-{}".format(self.app.name, crc)

    def _make_licence_volume_configs(self):
        """Return volume config for the licence secret."""
        config = self.model.config
        if not config["licence"]:
            return []
        return [
            {
                "name": "licence",
                "mountPath": "/secrets",
                "secret": {
                    "name": self._get_licence_secret_name(),
                    "files": [
                        {"key": LICENSE_SECRET_KEY_NAME, "path": "licence.txt", "mode": 0o444}
                    ],
                },
            }
        ]

    def _make_licence_k8s_secrets(self):
        """Return secret for the licence."""
        config = self.model.config
        if not config["licence"]:
            return []
        return [
            {
                "name": self._get_licence_secret_name(),
                "type": "Opaque",
                "stringData": {LICENSE_SECRET_KEY_NAME: config["licence"]},
            }
        ]

    def _update_pod_spec_for_licence(self, pod_spec):
        """Update pod_spec to make the licence, if configured, available to Mattermost."""
        config = self.model.config
        if not config["licence"]:
            return

        secrets = pod_spec["kubernetesResources"].get("secrets", [])
        secrets = extend_list_merging_dicts_matched_by_key(
            secrets, self._make_licence_k8s_secrets(), key="name"
        )
        pod_spec["kubernetesResources"]["secrets"] = secrets

        container = get_container(pod_spec, self.app.name)
        volume_config = container.get("volumeConfig", [])
        volume_config = extend_list_merging_dicts_matched_by_key(
            volume_config, self._make_licence_volume_configs(), key="name"
        )
        container["volumeConfig"] = volume_config

        get_env_config(pod_spec, self.app.name).update(
            {"MM_SERVICESETTINGS_LICENSEFILELOCATION": "/secrets/licence.txt"},
        )

    def configure_pod(self, event):
        """Assemble the pod spec and apply it, if possible."""
        if not self.state.db_uri:
            self.unit.status = WaitingStatus("Waiting for database relation")
            event.defer()
            return

        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return

        problems = self._check_for_config_problems()
        if problems:
            self.unit.status = BlockedStatus(problems)
            return

        self.unit.status = MaintenanceStatus("Assembling pod spec")
        pod_spec = self._make_pod_spec()

        get_env_config(pod_spec, self.app.name).update(
            environment.generate(
                self.model.config, self.app.name, self._site_url, self.state.db_uri
            )
        )

        self._update_pod_spec_for_k8s_ingress(pod_spec)
        self._update_pod_spec_for_licence(pod_spec)

        self.unit.status = MaintenanceStatus("Setting pod spec")
        self.model.pod.set_spec(pod_spec)
        self.unit.status = ActiveStatus()

    # This function was kept here to keep some older tests for now
    def _make_pod_config(self):
        return environment.generate(
            self.model.config, self.app.name, self._site_url, self.state.db_uri
        )


if __name__ == "__main__":
    main(MattermostK8sCharm, use_juju_for_storage=True)
