#!/usr/bin/env python3

import sys
sys.path.append('lib')
from ops.charm import CharmBase  # NoQA: E402
from ops.framework import StoredState  # NoQA: E402
from ops.main import main  # NoQA: E402
from ops.model import (  # NoQA: E402
    ActiveStatus,
    MaintenanceStatus,
    WaitingStatus,
)

from oci_image import OCIImageResource

import logging  # NoQA: E402
logger = logging.getLogger()


class MattermostK8sCharm(CharmBase):

    state = StoredState()

    def __init__(self, framework, key):
        super().__init__(framework, key)
        # get our mattermost_image from juju
        # ie: juju deploy . --resource mattermost_image=mattermost:latest )
        self.mattermost_image = OCIImageResource(self, 'mattermost_image')
        self.framework.observe(self.on.start, self.configure_pod)
        self.framework.observe(self.on.config_changed, self.configure_pod)
        self.framework.observe(self.on.leader_elected, self.configure_pod)
        self.framework.observe(self.on.upgrade_charm, self.configure_pod)

    def configure_pod(self, event):
        if not self.framework.model.unit.is_leader():
            self.model.unit.status = WaitingStatus('Not a leader')
            return

        mattermost_image_details = self.mattermost_image.fetch()
        self.model.unit.status = MaintenanceStatus('Configuring pod')
        config = self.model.config
        self.model.pod.set_spec({
            'containers': [{
                'name': self.framework.model.app.name,
                'imageDetails': mattermost_image_details,
                'ports': [{
                    'containerPort': int(self.framework.model.config['mattermost_port']),
                    'protocol': 'TCP',
                }],
                'config': {
                    'MATTERMOST_HTTPD_LISTEN_PORT': int(config['mattermost_port']),
                    'DB_HOST': config['pg_db_host'],
                    'DB_PORT_NUMBER': int(config['pg_db_port']),
                    'MM_USERNAME': config['pg_user'],
                    'MM_PASSWORD': config['pg_password'],
                    'MM_ENABLEOPENSERVER': config['open_server'],
                },
            }]
        })
        self.state.is_started = True
        self.model.unit.status = ActiveStatus()
 

if __name__ == '__main__':
    main(MattermostK8sCharm)
