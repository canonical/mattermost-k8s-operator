# Copyright 2023 Canonical Ltd.
# see LICENCE file for details.

"""General configuration module for tests."""
import pytest


def pytest_addoption(parser: pytest.Parser):
    """Process parameters for integration tests.

    Args:
        parser: Pytest parser used to add arguments to console commands
    """
    # Localstack instance IP
    parser.addoption("--localstack-ip", action="store", default="")
    # OCI image of mattermost
    parser.addoption("--mattermost-image", action="store", default="")
    # Kubernetes cluster configuration file
    parser.addoption("--kube-config", action="store", default="")
