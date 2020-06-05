#!/usr/bin/env python3

import copy
import unittest
import sys

sys.path.append('lib')  # noqa: E402
sys.path.append('src')  # noqa: E402

from charm import (
    MattermostK8sCharm,
    check_ranges,
)

from ops import testing

CONFIG_IMAGE_NO_CREDS = {
    'clustering': False,
    'mattermost_image_path': 'example.com/mattermost:latest',
    'mattermost_image_username': '',
    'mattermost_image_password': '',
    's3_enabled': False,
    'sso': False,
}

CONFIG_IMAGE_NO_IMAGE = {
    'clustering': False,
    'mattermost_image_path': '',
    'mattermost_image_username': '',
    'mattermost_image_password': '',
    's3_enabled': False,
    'sso': False,
}

CONFIG_IMAGE_NO_PASSWORD = {
    'clustering': False,
    'mattermost_image_path': 'example.com/mattermost:latest',
    'mattermost_image_username': 'production',
    'mattermost_image_password': '',
    's3_enabled': False,
    'sso': False,
}

CONFIG_NO_S3_SETTINGS_S3_ENABLED = {
    'clustering': False,
    'mattermost_image_path': 'example.com/mattermost:latest',
    'mattermost_image_username': '',
    'mattermost_image_password': '',
    's3_enabled': True,
    's3_endpoint': 's3.amazonaws.com',
    's3_bucket': '',
    's3_region': '',
    's3_access_key_id': '',
    's3_secret_access_key': '',
    'sso': False,
}

CONFIG_NO_S3_SETTINGS_S3_DISABLED_NO_DEFAULTS = {
    'clustering': False,
    'mattermost_image_path': 'example.com/mattermost:latest',
    'mattermost_image_username': '',
    'mattermost_image_password': '',
    's3_enabled': False,
    'sso': False,
}

RANGE_BAD = '10.242.0.0/8,91.189.92.242/25'
RANGE_GOOD = '10.0.0.0/8,91.189.92.128/25'
RANGE_MIXED = '10.242.0.0/8,91.189.92.128/25'


class TestMattermostK8sCharm(unittest.TestCase):

    def setUp(self):
        self.harness = testing.Harness(MattermostK8sCharm)
        self.harness.begin()

    def test_missing_charm_settings_image_no_creds(self):
        """Credentials are optional."""
        self.harness.charm.model.config = copy.deepcopy(CONFIG_IMAGE_NO_CREDS)
        expected = []
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_missing_charm_settings_image_no_image(self):
        """Image path is required."""
        self.harness.charm.model.config = copy.deepcopy(CONFIG_IMAGE_NO_IMAGE)
        expected = sorted(['mattermost_image_path'])
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_missing_charm_settings_image_no_password(self):
        """Password is required when username is set."""
        self.harness.charm.model.config = copy.deepcopy(CONFIG_IMAGE_NO_PASSWORD)
        expected = sorted(['mattermost_image_password'])
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_missing_charm_settings_no_s3_settings_s3_enabled(self):
        """If S3 is enabled, we need lots of settings to be set."""
        self.harness.charm.model.config = copy.deepcopy(CONFIG_NO_S3_SETTINGS_S3_ENABLED)
        expected = sorted(['s3_bucket', 's3_region', 's3_access_key_id', 's3_secret_access_key'])
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_missing_charm_settings_no_s3_settings_s3_disabled_no_defaults(self):
        """If S3 is not enabled, we don't care about any of the other S3 settings."""
        self.harness.charm.model.config = copy.deepcopy(CONFIG_NO_S3_SETTINGS_S3_DISABLED_NO_DEFAULTS)
        expected = []
        self.assertEqual(sorted(self.harness.charm._missing_charm_settings()), expected)

    def test_check_ranges_bad(self):
        """Host bits must not be set."""
        expected = 'range_bad: invalid network(s): 10.242.0.0/8, 91.189.92.242/25'
        self.assertEqual(check_ranges(RANGE_BAD, 'range_bad'), expected)

    def test_check_ranges_good(self):
        """CIDRs with the host bits unset are network addresses."""
        expected = None
        self.assertEqual(check_ranges(RANGE_GOOD, 'range_good'), expected)

    def test_check_ranges_mixed(self):
        """Any CIDRs that has host bits set must be rejected, even if others are OK."""
        expected = 'range_mixed: invalid network(s): 10.242.0.0/8'
        self.assertEqual(check_ranges(RANGE_MIXED, 'range_mixed'), expected)
