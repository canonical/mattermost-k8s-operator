#!/usr/bin/env python3

import copy
import unittest
import sys

sys.path.append('lib')  # noqa: E402
sys.path.append('src')  # noqa: E402

from charm import MattermostK8sCharm
from ops import testing

CONFIG_NO_S3_SETTINGS_S3_ENABLED = {
    's3_enabled': True,
    's3_endpoint': 's3.amazonaws.com',
    's3_bucket': '',
    's3_region': '',
    's3_access_key_id': '',
    's3_secret_access_key': '',
}

CONFIG_NO_S3_SETTINGS_S3_DISABLED_NO_DEFAULTS = {
    's3_enabled': False,
}


class TestMattermostK8sCharm(unittest.TestCase):

    def setUp(self):
        self.harness = testing.Harness(MattermostK8sCharm)
        self.harness.begin()

    def test_missing_charm_settings_no_s3_settings_s3_enabled(self):
        self.harness.charm.model.config = copy.deepcopy(CONFIG_NO_S3_SETTINGS_S3_ENABLED)
        expected = sorted(['s3_bucket', 's3_region', 's3_access_key_id', 's3_secret_access_key'])
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_missing_charm_settings_no_s3_settings_s3_disabled_no_defaults(self):
        self.harness.charm.model.config = copy.deepcopy(CONFIG_NO_S3_SETTINGS_S3_DISABLED_NO_DEFAULTS)
        expected = []
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)
