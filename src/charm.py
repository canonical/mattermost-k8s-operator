#!/usr/bin/env python3

# Copyright 2020 Canonical Ltd.
# Licensed under the GPLv3, see LICENCE file for details.

import os

from ipaddress import ip_network
from urllib.parse import urlparse
from zlib import crc32

from ops.charm import (
    CharmBase,
    CharmEvents,
)
from ops.framework import (
    EventBase,
    EventSource,
    StoredState,
)
from ops.main import main
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
    WaitingStatus,
)

from interface import pgsql

from utils import extend_list_merging_dicts_matched_by_key

import logging

logger = logging.getLogger()


# Mattermost's default port, and what we expect the image to use
CONTAINER_PORT = 8065
# Default port, enforced via envConfig to prevent operator error
METRICS_PORT = 8067
DATABASE_NAME = 'mattermost'
LICENCE_SECRET_KEY_NAME = 'licence'
REQUIRED_S3_SETTINGS = ['s3_bucket', 's3_region', 's3_access_key_id', 's3_secret_access_key']
REQUIRED_SETTINGS = ['mattermost_image_path']
REQUIRED_SSO_SETTINGS = ['licence', 'site_url']
SAML_IDP_CRT = 'saml-idp.crt'


class MattermostDBMasterAvailableEvent(EventBase):
    pass


class MattermostCharmEvents(CharmEvents):
    """Custom charm events."""

    db_master_available = EventSource(MattermostDBMasterAvailableEvent)


def check_ranges(ranges, name):
    """If ranges, a string comprising a comma-separated list of CIDRs, has
    one or more invalid elements, return a string describing the problem."""
    networks = ranges.split(',')
    invalid_networks = []
    for network in networks:
        try:
            ip_network(network)
        except ValueError:
            invalid_networks.append(network)
    if invalid_networks:
        return '{}: invalid network(s): {}'.format(name, ', '.join(invalid_networks))


def get_container(pod_spec, container_name):
    """Find and return the first container in pod_spec whose name is
    container_name, otherwise return None."""
    for container in pod_spec['containers']:
        if container['name'] == container_name:
            return container
    raise ValueError("Unable to find container named '{}' in pod spec".format(container_name))


def get_env_config(pod_spec, container_name):
    """Return the envConfig of the container in pod_spec whose name is
    container_name, otherwise return None.  If the container exists
    but has no envConfig, raise KeyError."""
    container = get_container(pod_spec, container_name)
    if 'envConfig' in container:
        return container['envConfig']
    else:
        raise ValueError("Unable to find envConfig for container named '{}'".format(container_name))


class MattermostK8sCharm(CharmBase):

    state = StoredState()
    on = MattermostCharmEvents()

    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(self.on.start, self.configure_pod)
        self.framework.observe(self.on.config_changed, self.configure_pod)
        self.framework.observe(self.on.leader_elected, self.configure_pod)
        self.framework.observe(self.on.upgrade_charm, self.configure_pod)

        # database
        self.state.set_default(db_conn_str=None, db_uri=None, db_ro_uris=[])
        self.db = pgsql.PostgreSQLClient(self, 'db')
        self.framework.observe(self.db.on.database_relation_joined, self._on_database_relation_joined)
        self.framework.observe(self.db.on.master_changed, self._on_master_changed)
        self.framework.observe(self.db.on.standby_changed, self._on_standby_changed)
        self.framework.observe(self.on.db_master_available, self.configure_pod)

    def _on_database_relation_joined(self, event: pgsql.DatabaseRelationJoinedEvent):
        """Handle db-relation-joined."""
        if self.model.unit.is_leader():
            # Provide requirements to the PostgreSQL server.
            event.database = DATABASE_NAME  # Request database named mydbname
            # event.extensions = ['citext']  # Request the citext extension installed
        elif event.database != DATABASE_NAME:
            # Leader has not yet set requirements. Defer, incase this unit
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
        """Check for some simple configuration problems and return a
        string describing them, otherwise return an empty string."""
        problems = []

        missing = self._missing_charm_settings()
        if missing:
            problems.append('required setting(s) empty: {}'.format(', '.join(sorted(missing))))

        ranges = self.model.config['ingress_whitelist_source_range']
        if ranges:
            problems.append(check_ranges(ranges, 'ingress_whitelist_source_range'))

        return '; '.join(filter(None, problems))

    def _make_pod_spec(self):
        """Return a pod spec with some core configuration."""
        config = self.model.config
        mattermost_image_details = {
            'imagePath': config['mattermost_image_path'],
        }
        if config['mattermost_image_username']:
            mattermost_image_details.update(
                {'username': config['mattermost_image_username'], 'password': config['mattermost_image_password']}
            )
        pod_config = self._make_pod_config()
        pod_config.update(self._make_s3_pod_config())

        return {
            'version': 3,  # otherwise resources are ignored
            'containers': [
                {
                    'name': self.app.name,
                    'imageDetails': mattermost_image_details,
                    'ports': [{'containerPort': CONTAINER_PORT, 'protocol': 'TCP'}],
                    'envConfig': pod_config,
                    'kubernetes': {
                        'readinessProbe': {'httpGet': {'path': '/api/v4/system/ping', 'port': CONTAINER_PORT}},
                    },
                }
            ],
        }

    def _make_pod_config(self):
        """Return an envConfig with some core configuration."""
        config = self.model.config
        # https://github.com/mattermost/mattermost-server/pull/14666
        db_uri = self.state.db_uri.replace('postgresql://', 'postgres://')
        pod_config = {
            'MATTERMOST_HTTPD_LISTEN_PORT': CONTAINER_PORT,
            'MM_CONFIG': db_uri,
            'MM_SQLSETTINGS_DATASOURCE': db_uri,
            # image proxy
            'MM_IMAGEPROXYSETTINGS_ENABLE': 'true' if config['image_proxy_enabled'] else 'false',
            'MM_IMAGEPROXYSETTINGS_IMAGEPROXYTYPE': 'local',
            # logging
            'MM_LOGSETTINGS_CONSOLELEVEL': 'DEBUG' if config['debug'] else 'INFO',
            'MM_LOGSETTINGS_ENABLECONSOLE': 'true',
            'MM_LOGSETTINGS_ENABLEFILE': 'false',
        }

        if config['primary_team']:
            pod_config['MM_TEAMSETTINGS_EXPERIMENTALPRIMARYTEAM'] = config['primary_team']

        if config['site_url']:
            pod_config['MM_SERVICESETTINGS_SITEURL'] = config['site_url']

        if config['outbound_proxy']:
            pod_config['HTTP_PROXY'] = config['outbound_proxy']
            pod_config['HTTPS_PROXY'] = config['outbound_proxy']
            if config['outbound_proxy_exceptions']:
                pod_config['NO_PROXY'] = config['outbound_proxy_exceptions']

        return pod_config

    def _missing_charm_settings(self):
        """Check configuration setting dependencies and return a list of
        missing settings; otherwise return an empty list."""
        config = self.model.config
        missing = []

        missing.extend([setting for setting in REQUIRED_SETTINGS if not config[setting]])

        if config['clustering'] and not config['licence']:
            missing.append('licence')

        if config['mattermost_image_username'] and not config['mattermost_image_password']:
            missing.append('mattermost_image_password')

        if config['performance_monitoring_enabled'] and not config['licence']:
            missing.append('licence')

        if config['s3_enabled']:
            missing.extend([setting for setting in REQUIRED_S3_SETTINGS if not config[setting]])

        if config['s3_server_side_encryption'] and not config['licence']:
            missing.append('licence')

        if config['sso']:
            missing.extend([setting for setting in REQUIRED_SSO_SETTINGS if not config[setting]])

        return sorted(list(set(missing)))

    def _make_s3_pod_config(self):
        """Return an envConfig of S3 settings, if any."""
        config = self.model.config
        if not config['s3_enabled']:
            return {}

        return {
            'MM_FILESETTINGS_DRIVERNAME': 'amazons3',
            'MM_FILESETTINGS_MAXFILESIZE': str(config['max_file_size'] * 1048576),  # LP:1881227
            'MM_FILESETTINGS_AMAZONS3SSL': 'true',  # defaults to true; belt and braces
            'MM_FILESETTINGS_AMAZONS3ENDPOINT': config['s3_endpoint'],
            'MM_FILESETTINGS_AMAZONS3BUCKET': config['s3_bucket'],
            'MM_FILESETTINGS_AMAZONS3REGION': config['s3_region'],
            'MM_FILESETTINGS_AMAZONS3ACCESSKEYID': config['s3_access_key_id'],
            'MM_FILESETTINGS_AMAZONS3SECRETACCESSKEY': config['s3_secret_access_key'],
            'MM_FILESETTINGS_AMAZONS3SSE': 'true' if config['s3_server_side_encryption'] else 'false',
            'MM_FILESETTINGS_AMAZONS3TRACE': 'true' if config['debug'] else 'false',
        }

    def _update_pod_spec_for_k8s_ingress(self, pod_spec):
        """Add resources to pod_spec configuring site ingress, if needed."""
        site_url = self.model.config['site_url']
        if not site_url:
            return

        parsed = urlparse(site_url)

        if not parsed.scheme.startswith('http'):
            return

        annotations = {'nginx.ingress.kubernetes.io/proxy-body-size': '{}m'.format(self.model.config['max_file_size'])}
        ingress = {
            "name": "{}-ingress".format(self.app.name),
            "spec": {
                "rules": [
                    {
                        "host": parsed.hostname,
                        "http": {
                            "paths": [
                                {"path": "/", "backend": {"serviceName": self.app.name, "servicePort": CONTAINER_PORT}}
                            ]
                        },
                    }
                ]
            },
        }
        if parsed.scheme == 'https':
            ingress['spec']['tls'] = [{'hosts': [parsed.hostname]}]
            tls_secret_name = self.model.config['tls_secret_name']
            if tls_secret_name:
                ingress['spec']['tls'][0]['secretName'] = tls_secret_name
        else:
            annotations['nginx.ingress.kubernetes.io/ssl-redirect'] = 'false'

        ingress_whitelist_source_range = self.model.config['ingress_whitelist_source_range']
        if ingress_whitelist_source_range:
            annotations['nginx.ingress.kubernetes.io/whitelist-source-range'] = ingress_whitelist_source_range

        if annotations:
            ingress['annotations'] = annotations

        # Due to https://github.com/canonical/operator/issues/293 we
        # can't use pod.set_spec's k8s_resources argument.
        resources = pod_spec.get('kubernetesResources', {})
        resources['ingressResources'] = [ingress]
        pod_spec['kubernetesResources'] = resources

    def _get_licence_secret_name(self):
        """Compute a content-dependent name for the licence secret.
        The name is varied so that licence updates cause the pods to
        be respawned.  Mattermost reads the licence file on startup
        and updates the copy in the database, if necessary."""
        crc = '{:08x}'.format(crc32(self.model.config['licence'].encode('utf-8')))
        return '{}-licence-{}'.format(self.app.name, crc)

    def _make_licence_volume_configs(self):
        """Return volume config for the licence secret."""
        config = self.model.config
        if not config['licence']:
            return []
        return [
            {
                'name': 'licence',
                'mountPath': '/secrets',
                'secret': {
                    'name': self._get_licence_secret_name(),
                    'files': [{'key': LICENCE_SECRET_KEY_NAME, 'path': 'licence.txt', 'mode': 0o444}],
                },
            }
        ]

    def _make_licence_k8s_secrets(self):
        """Return secret for the licence."""
        config = self.model.config
        if not config['licence']:
            return []
        return [
            {
                'name': self._get_licence_secret_name(),
                'type': 'Opaque',
                'stringData': {LICENCE_SECRET_KEY_NAME: config['licence']},
            }
        ]

    def _update_pod_spec_for_licence(self, pod_spec):
        """Update pod_spec to make the licence, if configured, available to Mattermost."""
        config = self.model.config
        if not config['licence']:
            return

        secrets = pod_spec['kubernetesResources'].get('secrets', [])
        secrets = extend_list_merging_dicts_matched_by_key(secrets, self._make_licence_k8s_secrets(), key='name')
        pod_spec['kubernetesResources']['secrets'] = secrets

        container = get_container(pod_spec, self.app.name)
        volume_config = container.get('volumeConfig', [])
        volume_config = extend_list_merging_dicts_matched_by_key(
            volume_config, self._make_licence_volume_configs(), key='name'
        )
        container['volumeConfig'] = volume_config

        get_env_config(pod_spec, self.app.name).update(
            {'MM_SERVICESETTINGS_LICENSEFILELOCATION': '/secrets/licence.txt'},
        )

    def _update_pod_spec_for_canonical_defaults(self, pod_spec):
        """Update pod_spec with various Mattermost settings particular to
        Canonical's deployment that may also less generally useful."""
        config = self.model.config
        if not config['use_canonical_defaults']:
            return

        get_env_config(pod_spec, self.app.name).update(
            {
                # If this is off, users can't turn it on themselves.
                'MM_SERVICESETTINGS_CLOSEUNUSEDDIRECTMESSAGES': 'true',
                # This allows Matterhorn to use emoji and react to messages.
                'MM_SERVICESETTINGS_ENABLECUSTOMEMOJI': 'true',
                # If this is off, users can't turn it on themselves.
                'MM_SERVICESETTINGS_ENABLELINKPREVIEWS': 'true',
                # Matterhorn recommends the use of Personal Access Tokens.
                'MM_SERVICESETTINGS_ENABLEUSERACCESSTOKENS': 'true',
                # We'll use one large team.  Create and invite are
                # disabled in the System Scheme, found in the Permissions
                # section of the System Console.
                'MM_TEAMSETTINGS_MAXUSERSPERTEAM': '1000',
            }
        )

    def _update_pod_spec_for_clustering(self, pod_spec):
        """Update pod_spec with clustering settings.  Vary the cluster
        name on the application name so that blue/green deployments in
        the same model won't talk to each other."""
        config = self.model.config
        if not config['clustering']:
            return

        get_env_config(pod_spec, self.app.name).update(
            {
                "MM_CLUSTERSETTINGS_ENABLE": "true",
                "MM_CLUSTERSETTINGS_CLUSTERNAME": '{}-{}'.format(self.app.name, os.environ['JUJU_MODEL_UUID']),
                "MM_CLUSTERSETTINGS_USEIPADDRESS": "true",
            }
        )

    def _update_pod_spec_for_sso(self, pod_spec):
        """Update pod_spec with settings to use login.ubuntu.com via
        SAML for single sign-on.  SAML_IDP_CRT must be generated and
        installed manually by a human (see README.md)."""
        config = self.model.config
        if not config['sso'] or [setting for setting in REQUIRED_SSO_SETTINGS if not config[setting]]:
            return
        site_hostname = urlparse(config['site_url']).hostname

        get_env_config(pod_spec, self.app.name).update(
            {
                'MM_EMAILSETTINGS_ENABLESIGNINWITHEMAIL': 'false',
                'MM_EMAILSETTINGS_ENABLESIGNINWITHUSERNAME': 'false',
                'MM_EMAILSETTINGS_ENABLESIGNUPWITHEMAIL': 'false',
                'MM_SAMLSETTINGS_ENABLE': 'true',
                'MM_SAMLSETTINGS_IDPURL': 'https://login.ubuntu.com/saml/',
                'MM_SAMLSETTINGS_VERIFY': 'true',
                'MM_SAMLSETTINGS_ENCRYPT': 'false',  # per POC
                'MM_SAMLSETTINGS_IDPDESCRIPTORURL': 'https://login.ubuntu.com',
                'MM_SAMLSETTINGS_IDPMETADATAURL': 'https://login.ubuntu.com/+saml/metadata',
                'MM_SAMLSETTINGS_ASSERTIONCONSUMERSERVICEURL': 'https://{}/login/sso/saml'.format(site_hostname),
                'MM_SAMLSETTINGS_LOGINBUTTONTEXT': 'Ubuntu SSO',
                'MM_SAMLSETTINGS_EMAILATTRIBUTE': 'email',
                'MM_SAMLSETTINGS_USERNAMEATTRIBUTE': 'username',
                'MM_SAMLSETTINGS_IDATTRIBUTE': 'openid',
                'MM_SAMLSETTINGS_FIRSTNAMEATTRIBUTE': 'fullname',
                'MM_SAMLSETTINGS_LASTNAMEATTRIBUTE': '',
                'MM_SAMLSETTINGS_IDPCERTIFICATEFILE': SAML_IDP_CRT,
                # Otherwise we have to install xmlsec1 and Mattermost forks on every login(!).
                'MM_EXPERIMENTALSETTINGS_USENEWSAMLLIBRARY': 'true',
            }
        )

    def _update_pod_spec_for_performance_monitoring(self, pod_spec):
        """Update pod_spec with settings for the Prometheus exporter."""
        config = self.model.config
        if not config['performance_monitoring_enabled']:
            return

        get_env_config(pod_spec, self.app.name).update(
            {
                'MM_METRICSSETTINGS_ENABLE': 'true' if config['performance_monitoring_enabled'] else 'false',
                'MM_METRICSSETTINGS_LISTENADDRESS': ':{}'.format(METRICS_PORT),
            }
        )

        # Ordinarily pods are selected for scraping by the in-cluster
        # Prometheus based on their annotations.  Unfortunately Juju
        # doesn't support pod annotations yet (LP:1884177).  When it
        # does, here are the annotations we'll need to add:

        # [ fetch or create annotations dict ]
        # annotations.update({
        #     # This is the prefix Canonical uses for Prometheus.
        #     # Upstream's position is that there is no default.
        #     'prometheus.io/port': str(METRICS_PORT),  # annotation values are strings
        #     'prometheus.io/scrape': 'true',
        # })
        # [ store annotations in pod_spec ]

    def _update_pod_spec_for_push(self, pod_spec):
        """Update pod_spec with settings for push notifications via
        Mattermost HPNS (hosted push notification service)."""
        config = self.model.config
        if not config['push_notification_server']:
            return
        contents = 'full' if config['push_notifications_include_message_snippet'] else 'id_loaded'

        get_env_config(pod_spec, self.app.name).update(
            {
                'MM_EMAILSETTINGS_SENDPUSHNOTIFICATIONS': 'true',
                'MM_EMAILSETTINGS_PUSHNOTIFICATIONCONTENTS': contents,
                'MM_EMAILSETTINGS_PUSHNOTIFICATIONSERVER': config['push_notification_server'],
            }
        )

    def _update_pod_spec_for_smtp(self, pod_spec):
        """Update pod_spec with settings for an outgoing SMTP relay."""
        config = self.model.config
        if not config['smtp_host']:
            return

        get_env_config(pod_spec, self.app.name).update(
            {'MM_EMAILSETTINGS_SMTPPORT': 25, 'MM_EMAILSETTINGS_SMTPSERVER': config['smtp_host']}
        )

    def configure_pod(self, event):
        """Assemble the pod spec and apply it, if possible."""
        if not self.state.db_uri:
            self.unit.status = WaitingStatus('Waiting for database relation')
            event.defer()
            return

        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return

        problems = self._check_for_config_problems()
        if problems:
            self.unit.status = BlockedStatus(problems)
            return

        self.unit.status = MaintenanceStatus('Assembling pod spec')
        pod_spec = self._make_pod_spec()
        self._update_pod_spec_for_canonical_defaults(pod_spec)
        self._update_pod_spec_for_clustering(pod_spec)
        self._update_pod_spec_for_k8s_ingress(pod_spec)
        self._update_pod_spec_for_licence(pod_spec)
        self._update_pod_spec_for_performance_monitoring(pod_spec)
        self._update_pod_spec_for_push(pod_spec)
        self._update_pod_spec_for_sso(pod_spec)
        self._update_pod_spec_for_smtp(pod_spec)

        self.unit.status = MaintenanceStatus('Setting pod spec')
        self.model.pod.set_spec(pod_spec)
        self.unit.status = ActiveStatus()


if __name__ == '__main__':
    main(MattermostK8sCharm, use_juju_for_storage=True)
