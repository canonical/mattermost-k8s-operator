#!/usr/bin/env python3

import sys
sys.path.append('lib')  # noqa: E402

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

    def configure_pod(self, event):
        if not self.state.db_uri:
            self.model.unit.status = WaitingStatus('Waiting for database relation')
            event.defer()
            return

        if not self.framework.model.unit.is_leader():
            self.model.unit.status = WaitingStatus('Not a leader')
            return

        mattermost_image_details = self.mattermost_image.fetch()
        self.model.unit.status = MaintenanceStatus('Configuring pod')
        config = self.model.config

        pod_config = {
            'MATTERMOST_HTTPD_LISTEN_PORT': int(config['mattermost_port']),
            'MM_SQLSETTINGS_DATASOURCE': self.state.db_uri,
            'MM_ENABLEOPENSERVER': config['open_server'],
        }

        if config['site_url']:
            pod_config['MM_SERVICESETTINGS_SITEURL'] = config['site_url']

        self.model.pod.set_spec({
            'containers': [{
                'name': self.framework.model.app.name,
                'imageDetails': mattermost_image_details,
                'ports': [{
                    'containerPort': int(self.framework.model.config['mattermost_port']),
                    'protocol': 'TCP',
                }],
                'config': pod_config,
            }]
        })
        self.state.is_started = True
        self.model.unit.status = ActiveStatus()


if __name__ == '__main__':
    main(MattermostK8sCharm)
