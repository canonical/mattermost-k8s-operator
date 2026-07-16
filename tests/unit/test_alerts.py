# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://ops.readthedocs.io/en/latest/explanation/testing.html

"""Unit tests for alert rules."""

import os
import shutil
import subprocess
import pytest


@pytest.mark.skipif(
    not shutil.which("promtool"),
    reason="promtool CLI tool not installed on this system",
)
def test_prometheus_alert_rules():
    """
    arrange: A defined set of Prometheus alert rules and a mock data test file.
    act: Run the promtool unit testing engine via a subprocess call.
    assert: The promtool exit code is 0, indicating all alert rules match the
        expected firing states based on the mock metrics.
    """
    test_file_path = os.path.join("tests", "unit", "test_prometheus_alerts.yaml")

    result = subprocess.run(
        ["promtool", "test", "rules", test_file_path],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Promtool verification failed:\n{result.stderr}\n{result.stdout}"