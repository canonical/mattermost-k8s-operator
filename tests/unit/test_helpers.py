import unittest

from charm import (
    check_ranges,
    get_container,
    get_env_config,
)

POD_SPEC_MULTIPLE_CONTAINERS = {
    'containers': [
        {'name': 'one', 'envConfig': {'THIS_CONTAINER': 'one'}},
        {'name': 'two', 'envConfig': {'THIS_CONTAINER': 'two'}},
        {'name': 'three', 'envConfig': {'THIS_CONTAINER': 'three'}},
    ]
}

POD_SPEC_NO_ENVCONFIG = {'containers': [{'name': 'one'}]}

RANGE_BAD = '10.242.0.0/8,91.189.92.242/25'
RANGE_GOOD = '10.0.0.0/8,91.189.92.128/25'
RANGE_MIXED = '10.242.0.0/8,91.189.92.128/25'


class TestMattermostCharmHelpers(unittest.TestCase):
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

    def test_get_container(self):
        """The container with matching name is returned."""
        expected = {'name': 'two', 'envConfig': {'THIS_CONTAINER': 'two'}}
        self.assertEqual(get_container(POD_SPEC_MULTIPLE_CONTAINERS, 'two'), expected)

    def test_get_container_nonexistent(self):
        """No matching container returns None."""
        self.assertEqual(get_container(POD_SPEC_MULTIPLE_CONTAINERS, 'eleventy-ten'), None)

    def test_get_env_config(self):
        """The envConfig of the container with the matching name is returned."""
        expected = {'THIS_CONTAINER': 'two'}
        self.assertEqual(get_env_config(POD_SPEC_MULTIPLE_CONTAINERS, 'two'), expected)

    def test_get_env_config_nonexistent_container(self):
        """No matching container returns None."""
        self.assertEqual(get_env_config(POD_SPEC_MULTIPLE_CONTAINERS, 'eleventy-ten'), None)

    def test_get_env_config_container_no_envconfig(self):
        """Container with no envConfig raises KeyError."""
        # Not necessarily a good design, but if it's changed this will remind us to update the test suite.
        with self.assertRaises(KeyError):
            get_env_config(POD_SPEC_NO_ENVCONFIG, 'one')
