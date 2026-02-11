#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests."""

import logging

import jubilant
import pytest

logger = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
def test_charm(juju: jubilant.Juju):
    """
    arrange:
    act:
    assert:
    """
    _ = juju.status()
    assert True
