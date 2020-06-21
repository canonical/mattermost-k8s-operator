import sys
sys.path.append('lib')  # noqa: E402
sys.path.append('src')  # noqa: E402

import unittest

from charm import (
    MattermostK8sCharm,
    METRICS_PORT,
)

from ops import testing

CONFIG_IMAGE_NO_CREDS = {
    'clustering': False,
    'mattermost_image_path': 'example.com/mattermost:latest',
    'mattermost_image_username': '',
    'mattermost_image_password': '',
    'performance_monitoring_enabled': False,
    's3_enabled': False,
    's3_server_side_encryption': False,
    'sso': False,
}

CONFIG_IMAGE_NO_IMAGE = {
    'clustering': False,
    'mattermost_image_path': '',
    'mattermost_image_username': '',
    'mattermost_image_password': '',
    'performance_monitoring_enabled': False,
    's3_enabled': False,
    's3_server_side_encryption': False,
    'sso': False,
}

CONFIG_IMAGE_NO_PASSWORD = {
    'clustering': False,
    'mattermost_image_path': 'example.com/mattermost:latest',
    'mattermost_image_username': 'production',
    'mattermost_image_password': '',
    'performance_monitoring_enabled': False,
    's3_enabled': False,
    's3_server_side_encryption': False,
    'sso': False,
}

CONFIG_LICENCE_SECRET = {"licence": "RANDOMSTRING"}

CONFIG_NO_LICENCE_SECRET = {"licence": ""}

CONFIG_NO_S3_SETTINGS_S3_ENABLED = {
    'clustering': False,
    'mattermost_image_path': 'example.com/mattermost:latest',
    'mattermost_image_username': '',
    'mattermost_image_password': '',
    'performance_monitoring_enabled': False,
    's3_enabled': True,
    's3_endpoint': 's3.amazonaws.com',
    's3_bucket': '',
    's3_region': '',
    's3_access_key_id': '',
    's3_secret_access_key': '',
    's3_server_side_encryption': False,
    'sso': False,
}

CONFIG_NO_S3_SETTINGS_S3_DISABLED_NO_DEFAULTS = {
    'clustering': False,
    'mattermost_image_path': 'example.com/mattermost:latest',
    'mattermost_image_username': '',
    'mattermost_image_password': '',
    'performance_monitoring_enabled': False,
    's3_enabled': False,
    's3_server_side_encryption': False,
    'sso': False,
}

CONFIG_PUSH_NOTIFICATION_SERVER_UNSET = {
    'push_notification_server': '',
}

CONFIG_PUSH_NOTIFICATION_NO_MESSAGE_SNIPPET = {
    'push_notification_server': 'https://push.mattermost.com/',
    'push_notifications_include_message_snippet': False,
}

CONFIG_PUSH_NOTIFICATION_MESSAGE_SNIPPET = {
    'push_notification_server': 'https://push.mattermost.com/',
    'push_notifications_include_message_snippet': True,
}


class TestMattermostK8sCharmHooksDisabled(unittest.TestCase):

    def setUp(self):
        self.harness = testing.Harness(MattermostK8sCharm)
        self.harness.begin()
        self.harness.disable_hooks()

    def test_missing_charm_settings_image_no_creds(self):
        """Credentials are optional."""
        self.harness.update_config(CONFIG_IMAGE_NO_CREDS)
        expected = []
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_missing_charm_settings_image_no_image(self):
        """Image path is required."""
        self.harness.update_config(CONFIG_IMAGE_NO_IMAGE)
        expected = sorted(['mattermost_image_path'])
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_missing_charm_settings_image_no_password(self):
        """Password is required when username is set."""
        self.harness.update_config(CONFIG_IMAGE_NO_PASSWORD)
        expected = sorted(['mattermost_image_password'])
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_missing_charm_settings_no_s3_settings_s3_enabled(self):
        """If S3 is enabled, we need lots of settings to be set."""
        self.harness.update_config(CONFIG_NO_S3_SETTINGS_S3_ENABLED)
        expected = sorted(['s3_bucket', 's3_region', 's3_access_key_id', 's3_secret_access_key'])
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_missing_charm_settings_no_s3_settings_s3_disabled_no_defaults(self):
        """If S3 is not enabled, we don't care about any of the other S3 settings."""
        self.harness.update_config(CONFIG_NO_S3_SETTINGS_S3_DISABLED_NO_DEFAULTS)
        expected = []
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_push_notification_server_unset(self):
        """If push_notification_server is set to an empty string (default) don't update spec"""
        self.harness.update_config(CONFIG_PUSH_NOTIFICATION_SERVER_UNSET)
        expected = {}
        pod_spec = {}
        self.assertEqual(self.harness.charm._update_pod_spec_for_push(pod_spec), expected)

    def test_push_notification_no_message_snippet(self):
        """Push notification configured, but without message snippets"""
        self.harness.update_config(CONFIG_PUSH_NOTIFICATION_NO_MESSAGE_SNIPPET)
        expected = {
            'containers': [{
                'name': 'mattermost',
                'envConfig': {
                    'MM_EMAILSETTINGS_SENDPUSHNOTIFICATIONS': 'true',
                    'MM_EMAILSETTINGS_PUSHNOTIFICATIONCONTENTS': 'id_loaded',
                    'MM_EMAILSETTINGS_PUSHNOTIFICATIONSERVER': 'https://push.mattermost.com/',
                }
            }],
        }
        pod_spec = {
            'containers': [{
                'name': 'mattermost',
                'envConfig': {},
            }],
        }
        self.assertEqual(self.harness.charm._update_pod_spec_for_push(pod_spec), expected)

    def test_push_notification_message_snippet(self):
        """Push notifications configured, including message snippets"""
        self.harness.update_config(CONFIG_PUSH_NOTIFICATION_MESSAGE_SNIPPET)
        expected = {
            'containers': [{
                'name': 'mattermost',
                'envConfig': {
                    'MM_EMAILSETTINGS_SENDPUSHNOTIFICATIONS': 'true',
                    'MM_EMAILSETTINGS_PUSHNOTIFICATIONCONTENTS': 'full',
                    'MM_EMAILSETTINGS_PUSHNOTIFICATIONSERVER': 'https://push.mattermost.com/',
                }
            }],
        }
        pod_spec = {
            'containers': [{
                'name': 'mattermost',
                'envConfig': {},
            }],
        }
        self.assertEqual(self.harness.charm._update_pod_spec_for_push(pod_spec), expected)

    def test_get_licence_secret_name(self):
        """Test the licence secret name is correctly constructed"""
        self.harness.update_config(CONFIG_LICENCE_SECRET)
        self.assertEqual(self.harness.charm._get_licence_secret_name(), "mattermost-licence-b5bbb1bf")

    def test_make_licence_k8s_secrets(self):
        """Test making licence k8s secrets"""
        self.harness.update_config(CONFIG_NO_LICENCE_SECRET)
        self.assertEqual(self.harness.charm._make_licence_k8s_secrets(), [])
        self.harness.update_config(CONFIG_LICENCE_SECRET)
        expected = [{
            'name': 'mattermost-licence-b5bbb1bf',
            'type': 'Opaque',
            'stringData': {
                'licence': 'RANDOMSTRING',
            },
        }]
        self.assertEqual(self.harness.charm._make_licence_k8s_secrets(), expected)

    def test_make_licence_volume_configs(self):
        """Test making licence volume configs"""
        self.harness.update_config(CONFIG_NO_LICENCE_SECRET)
        self.assertEqual(self.harness.charm._make_licence_volume_configs(), [])
        self.harness.update_config(CONFIG_LICENCE_SECRET)
        expected = [{
            'name': 'licence',
            'mountPath': '/secrets',
            'secret': {
                'name': 'mattermost-licence-b5bbb1bf',
                'files': [{
                    'key': 'licence',
                    'path': 'licence.txt',
                    'mode': 0o444,
                }],
            },
        }]
        self.assertEqual(self.harness.charm._make_licence_volume_configs(), expected)

    def test_update_pod_spec_for_performance_monitoring(self):
        """envConfig is updated, and pre-existing annotations are not clobbered."""
        # We can't set annotations yet because of LP:1884177.
        # When we can, this test will need updating.
        self.harness.update_config({
            'performance_monitoring_enabled': True,
        })
        pod_spec = {
            'containers': [{
                'name': 'mattermost',
                'envConfig': {},
            }],
        }
        expected = {
            'containers': [{
                'name': 'mattermost',
                'envConfig': {
                    'MM_METRICSSETTINGS_ENABLE': 'true',
                    'MM_METRICSSETTINGS_LISTENADDRESS': ':{}'.format(METRICS_PORT),
                },
            }],
        }
        self.assertEqual(self.harness.charm._update_pod_spec_for_performance_monitoring(pod_spec), expected)
