# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""General configuration module for tests."""
import pytest


def pytest_addoption(parser: pytest.Parser):
    """Process parameters for integration tests.

    Args:
        parser: Pytest parser used to add arguments to console commands
    """
    parser.addoption("--charm-file", action="store")
    # Localstack instance URL
    parser.addoption("--localstack-url", action="store", default="")
    # OCI image of mattermost
    parser.addoption("--mattermost-image", action="store", default="")
    # Kubernetes cluster configuration file
    parser.addoption("--kube-config", action="store", default="")
