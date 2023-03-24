# Copyright 2023 Canonical Ltd.
# see LICENCE file for details.

"""General configuration module for tests."""
import pytest


def pytest_addoption(parser: pytest.Parser):
    """Process parameters for integration tests.

    Args:
        parser: Pytest parser used to add arguments to console commands
    """
    # # --openstack-rc points to an openstack credential file in the "rc" file style
    # # https://docs.openstack.org/newton/user-guide/common/cli-set-environment-variables-using-openstack-rc.html
    # parser.addoption("--openstack-rc", action="store", default="")
    parser.addoption("--localstack-ip", action="store", default="")
    parser.addoption("--mattermost-image", action="store", default="")
    # Kubernetes cluster configuration file
    parser.addoption("--kube-config", action="store", default="")
