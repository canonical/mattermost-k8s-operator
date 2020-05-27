#!/usr/bin/env python3

import sys
sys.path.append('lib')  # noqa: E402

from urllib.parse import urlparse

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
    MaintenanceStatus,
    WaitingStatus,
)

from interface import pgsql
from oci_image import OCIImageResource

import logging
logger = logging.getLogger()


CONTAINER_PORT = 8065  # Mattermost's default port, and what we expect the image to use
DATABASE_NAME = 'mattermost'


class MattermostDBMasterAvailableEvent(EventBase):
    pass


class MattermostCharmEvents(CharmEvents):
    """Custom charm events."""
    db_master_available = EventSource(MattermostDBMasterAvailableEvent)


class MattermostK8sCharm(CharmBase):

    state = StoredState()
    on = MattermostCharmEvents()

    def __init__(self, *args):
        super().__init__(*args)

        # get our mattermost_image from juju
        # ie: juju deploy . --resource mattermost_image=mattermost:latest )
        self.mattermost_image = OCIImageResource(self, 'mattermost_image')
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
        if event.database != DATABASE_NAME:
            # Leader has not yet set requirements. Wait until next
            # event, or risk connecting to an incorrect database.
            return

        self.state.db_ro_uris = [c.uri for c in event.standbys]

        # TODO(pjdc): Emit event when we add support for read replicas.

    def _make_pod_spec(self):
        mattermost_image_details = self.mattermost_image.fetch()
        pod_spec = {
            'version': 2,       # otherwise resources are ignored
            'containers': [{
                'name': self.app.name,
                'imageDetails': mattermost_image_details,
                'ports': [{
                    'containerPort': CONTAINER_PORT,
                    'protocol': 'TCP',
                }],
                'config': self._make_pod_config(),
            }]
        }

        return pod_spec

    def _make_pod_config(self):
        config = self.model.config
        # https://github.com/mattermost/mattermost-server/pull/14666
        db_uri = self.state.db_uri.replace('postgresql://', 'postgres://')
        pod_config = {
            'MATTERMOST_HTTPD_LISTEN_PORT': CONTAINER_PORT,
            'MM_CONFIG': db_uri,
            'MM_SQLSETTINGS_DATASOURCE': db_uri,
            'MM_ENABLEOPENSERVER': config['open_server'],
        }

        if config['site_url']:
            pod_config['MM_SERVICESETTINGS_SITEURL'] = config['site_url']

        return pod_config

    def _make_k8s_resources(self):
        site_url = self.model.config['site_url']
        if not site_url:
            return None
        parsed = urlparse(site_url)

        if parsed.scheme.startswith('http'):
            ingress = {
                "name": self.app.name,
                "spec": {
                    "rules": [{
                        "host": parsed.hostname,
                        "http": {
                            "paths": [{
                                "path": "/",
                                "backend": {
                                    "serviceName": self.app.name,
                                    "servicePort": CONTAINER_PORT,
                                }
                            }]
                        }
                    }]
                }
            }
            if parsed.scheme == 'https':
                ingress['spec']['tls'] = [
                    {
                        'hosts': [parsed.hostname],
                    }
                ]
                tls_secret_name = self.model.config['tls_secret_name']
                if tls_secret_name:
                    ingress['spec']['tls'][0]['secretName'] = tls_secret_name

            return {
                "kubernetesResources": {
                    "ingressResources": [ingress],
                }
            }

    def configure_pod(self, event):
        if not self.state.db_uri:
            self.unit.status = WaitingStatus('Waiting for database relation')
            event.defer()
            return

        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return

        self.unit.status = MaintenanceStatus('Configuring pod')

        pod_spec = self._make_pod_spec()

        # Due to https://github.com/canonical/operator/issues/293 we
        # can't use pod.set_spec's k8s_resources argument.
        k8s_resources = self._make_k8s_resources()
        if k8s_resources:
            pod_spec.update(k8s_resources)

        self.model.pod.set_spec(pod_spec)
        self.state.is_started = True
        self.unit.status = ActiveStatus()


if __name__ == '__main__':
    main(MattermostK8sCharm)
