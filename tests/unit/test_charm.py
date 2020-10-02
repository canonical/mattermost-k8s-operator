# Copyright 2020 Canonical Ltd.
# Licensed under the GPLv3, see LICENCE file for details.

import mock
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
    'debug': False,
    'mattermost_image_path': 'example.com/mattermost:latest',
    'mattermost_image_username': '',
    'mattermost_image_password': '',
    'max_file_size': 5,
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

CONFIG_LICENCE_REQUIRED_MIXED_INGRESS = {
    'clustering': True,
    'ingress_whitelist_source_range': '10.242.0.0/8,91.189.92.128/25',
    'licence': '',
    'mattermost_image_path': 'example.com/mattermost:latest',
    'mattermost_image_username': '',
    'mattermost_image_password': '',
    'performance_monitoring_enabled': False,
    's3_enabled': False,
    's3_server_side_encryption': False,
    'sso': False,
}


class TestMattermostK8sCharmHooksDisabled(unittest.TestCase):
    def setUp(self):
        self.harness = testing.Harness(MattermostK8sCharm)
        self.harness.begin()
        self.harness.disable_hooks()

    def test_check_for_config_problems(self):
        """Config problems as a string."""
        self.harness.update_config(CONFIG_LICENCE_REQUIRED_MIXED_INGRESS)
        expected = (
            'required setting(s) empty: licence; ingress_whitelist_source_range: invalid network(s): 10.242.0.0/8'
        )
        self.assertEqual(self.harness.charm._check_for_config_problems(), expected)

    def test_make_s3_pod_config(self):
        """Make s3 pod config."""
        self.harness.update_config(CONFIG_NO_S3_SETTINGS_S3_ENABLED)
        expected = {
            'MM_FILESETTINGS_DRIVERNAME': 'amazons3',
            'MM_FILESETTINGS_MAXFILESIZE': '5242880',
            'MM_FILESETTINGS_AMAZONS3SSL': 'true',
            'MM_FILESETTINGS_AMAZONS3ENDPOINT': 's3.amazonaws.com',
            'MM_FILESETTINGS_AMAZONS3BUCKET': '',
            'MM_FILESETTINGS_AMAZONS3REGION': '',
            'MM_FILESETTINGS_AMAZONS3ACCESSKEYID': '',
            'MM_FILESETTINGS_AMAZONS3SECRETACCESSKEY': '',
            'MM_FILESETTINGS_AMAZONS3SSE': 'false',
            'MM_FILESETTINGS_AMAZONS3TRACE': 'false',
        }
        self.assertEqual(self.harness.charm._make_s3_pod_config(), expected)

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
        self.harness.charm._update_pod_spec_for_push(pod_spec)
        self.assertEqual(pod_spec, expected)

    def test_push_notification_no_message_snippet(self):
        """Push notification configured, but without message snippets"""
        self.harness.update_config(CONFIG_PUSH_NOTIFICATION_NO_MESSAGE_SNIPPET)
        expected = {
            'containers': [
                {
                    'name': 'mattermost',
                    'envConfig': {
                        'MM_EMAILSETTINGS_SENDPUSHNOTIFICATIONS': 'true',
                        'MM_EMAILSETTINGS_PUSHNOTIFICATIONCONTENTS': 'id_loaded',
                        'MM_EMAILSETTINGS_PUSHNOTIFICATIONSERVER': 'https://push.mattermost.com/',
                    },
                }
            ],
        }
        pod_spec = {
            'containers': [{'name': 'mattermost', 'envConfig': {}}],
        }
        self.harness.charm._update_pod_spec_for_push(pod_spec)
        self.assertEqual(pod_spec, expected)

    def test_push_notification_message_snippet(self):
        """Push notifications configured, including message snippets"""
        self.harness.update_config(CONFIG_PUSH_NOTIFICATION_MESSAGE_SNIPPET)
        expected = {
            'containers': [
                {
                    'name': 'mattermost',
                    'envConfig': {
                        'MM_EMAILSETTINGS_SENDPUSHNOTIFICATIONS': 'true',
                        'MM_EMAILSETTINGS_PUSHNOTIFICATIONCONTENTS': 'full',
                        'MM_EMAILSETTINGS_PUSHNOTIFICATIONSERVER': 'https://push.mattermost.com/',
                    },
                }
            ],
        }
        pod_spec = {
            'containers': [{'name': 'mattermost', 'envConfig': {}}],
        }
        self.harness.charm._update_pod_spec_for_push(pod_spec)
        self.assertEqual(pod_spec, expected)

    def test_get_licence_secret_name(self):
        """Test the licence secret name is correctly constructed"""
        self.harness.update_config(CONFIG_LICENCE_SECRET)
        self.assertEqual(self.harness.charm._get_licence_secret_name(), "mattermost-licence-b5bbb1bf")

    def test_make_licence_k8s_secrets(self):
        """Test making licence k8s secrets"""
        self.harness.update_config(CONFIG_NO_LICENCE_SECRET)
        self.assertEqual(self.harness.charm._make_licence_k8s_secrets(), [])
        self.harness.update_config(CONFIG_LICENCE_SECRET)
        expected = [
            {'name': 'mattermost-licence-b5bbb1bf', 'type': 'Opaque', 'stringData': {'licence': 'RANDOMSTRING'}}
        ]
        self.assertEqual(self.harness.charm._make_licence_k8s_secrets(), expected)

    def test_make_licence_volume_configs(self):
        """Test making licence volume configs"""
        self.harness.update_config(CONFIG_NO_LICENCE_SECRET)
        self.assertEqual(self.harness.charm._make_licence_volume_configs(), [])
        self.harness.update_config(CONFIG_LICENCE_SECRET)
        expected = [
            {
                'name': 'licence',
                'mountPath': '/secrets',
                'secret': {
                    'name': 'mattermost-licence-b5bbb1bf',
                    'files': [{'key': 'licence', 'path': 'licence.txt', 'mode': 0o444}],
                },
            }
        ]
        self.assertEqual(self.harness.charm._make_licence_volume_configs(), expected)

    def test_update_pod_spec_for_k8s_ingress(self):
        """Test making the k8s ingress, and ensuring ingress name is different to app name

        We're specifically testing that the ingress name is not the same as
        the app name due to LP#1884674."""
        self.harness.update_config(
            {
                'ingress_whitelist_source_range': '',
                'max_file_size': 5,
                'site_url': 'https://chat.example.com',
                'tls_secret_name': 'chat-example-com-tls',
            }
        )
        ingress_name = 'mattermost-ingress'
        self.assertNotEqual(ingress_name, self.harness.charm.app.name)
        expected = {
            'kubernetesResources': {
                'ingressResources': [
                    {
                        'name': ingress_name,
                        'spec': {
                            'rules': [
                                {
                                    'host': 'chat.example.com',
                                    'http': {
                                        'paths': [
                                            {
                                                'path': '/',
                                                'backend': {'serviceName': 'mattermost', 'servicePort': 8065},
                                            }
                                        ]
                                    },
                                }
                            ],
                            'tls': [{'hosts': ['chat.example.com'], 'secretName': 'chat-example-com-tls'}],
                        },
                        'annotations': {'nginx.ingress.kubernetes.io/proxy-body-size': '5m'},
                    }
                ]
            }
        }
        pod_spec = {}
        self.harness.charm._update_pod_spec_for_k8s_ingress(pod_spec)
        self.assertEqual(pod_spec, expected)
        # And now test with an ingress_whitelist_source_range, and an http
        # rather than https site_url to test a few more ingress conditions.
        self.harness.update_config(
            {'ingress_whitelist_source_range': '10.10.10.10/24', 'site_url': 'http://chat.example.com'}
        )
        expected = {
            'kubernetesResources': {
                'ingressResources': [
                    {
                        'name': ingress_name,
                        'spec': {
                            'rules': [
                                {
                                    'host': 'chat.example.com',
                                    'http': {
                                        'paths': [
                                            {
                                                'path': '/',
                                                'backend': {'serviceName': 'mattermost', 'servicePort': 8065},
                                            }
                                        ]
                                    },
                                }
                            ],
                        },
                        'annotations': {
                            'nginx.ingress.kubernetes.io/proxy-body-size': '5m',
                            'nginx.ingress.kubernetes.io/ssl-redirect': 'false',
                            'nginx.ingress.kubernetes.io/whitelist-source-range': '10.10.10.10/24',
                        },
                    }
                ]
            }
        }
        pod_spec = {}
        self.harness.charm._update_pod_spec_for_k8s_ingress(pod_spec)
        self.assertEqual(pod_spec, expected)

    def test_update_pod_spec_for_performance_monitoring(self):
        """envConfig is updated, and pre-existing annotations are not clobbered."""
        # We can't set annotations yet because of LP:1884177.
        # When we can, this test will need updating.
        self.harness.update_config({'performance_monitoring_enabled': True})
        pod_spec = {
            'containers': [{'name': 'mattermost', 'envConfig': {}}],
        }
        expected = {
            'containers': [
                {
                    'name': 'mattermost',
                    'envConfig': {
                        'MM_METRICSSETTINGS_ENABLE': 'true',
                        'MM_METRICSSETTINGS_LISTENADDRESS': ':{}'.format(METRICS_PORT),
                    },
                }
            ],
        }
        self.harness.charm._update_pod_spec_for_performance_monitoring(pod_spec)
        self.assertEqual(pod_spec, expected)

    @mock.patch.dict('os.environ', {"JUJU_MODEL_UUID": "fakeuuid"})
    def test_update_pod_spec_for_clustering(self):
        """Test clustering config."""
        self.harness.update_config({'clustering': False})
        pod_spec = {}
        self.harness.charm._update_pod_spec_for_clustering(pod_spec)
        self.assertEqual(pod_spec, {})
        self.harness.update_config({'clustering': True})
        pod_spec = {
            'containers': [{'name': 'mattermost', 'envConfig': {}}],
        }
        expected = {
            'containers': [
                {
                    'name': 'mattermost',
                    'envConfig': {
                        'MM_CLUSTERSETTINGS_ENABLE': 'true',
                        'MM_CLUSTERSETTINGS_CLUSTERNAME': 'mattermost-fakeuuid',
                        'MM_CLUSTERSETTINGS_USEIPADDRESS': 'true',
                    },
                }
            ],
        }
        self.harness.charm._update_pod_spec_for_clustering(pod_spec)
        self.assertEqual(pod_spec, expected)

    def test_update_pod_spec_for_canonical_defaults(self):
        """Test canonical defaults."""
        self.harness.update_config({'use_canonical_defaults': False})
        pod_spec = {}
        self.harness.charm._update_pod_spec_for_canonical_defaults(pod_spec)
        self.assertEqual(pod_spec, {})
        self.harness.update_config({'use_canonical_defaults': True})
        pod_spec = {
            'containers': [{'name': 'mattermost', 'envConfig': {}}],
        }
        expected = {
            'containers': [
                {
                    'name': 'mattermost',
                    'envConfig': {
                        'MM_SERVICESETTINGS_CLOSEUNUSEDDIRECTMESSAGES': 'true',
                        'MM_SERVICESETTINGS_ENABLECUSTOMEMOJI': 'true',
                        'MM_SERVICESETTINGS_ENABLELINKPREVIEWS': 'true',
                        'MM_SERVICESETTINGS_ENABLEUSERACCESSTOKENS': 'true',
                        'MM_TEAMSETTINGS_MAXUSERSPERTEAM': '1000',
                    },
                }
            ],
        }
        self.harness.charm._update_pod_spec_for_canonical_defaults(pod_spec)
        self.assertEqual(pod_spec, expected)
