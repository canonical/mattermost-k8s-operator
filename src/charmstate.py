# Based on interface-pgsql/pgsql/pgsql.py

# Copyright 2020 Canonical Ltd.
# Licensed under the GPLv3, see LICENCE file for details.

import subprocess
import yaml


def _state_delete(attribute: str):
    """Delete attribute from controller-backed per-unit charm state."""
    cmd = ['state-delete', attribute]
    return yaml.safe_load(subprocess.check_output(cmd).decode('UTF-8'))


def _state_get(attribute: str):
    """Fetch the value of attribute from controller-backed per-unit charm state."""
    cmd = ['state-get', '--format=yaml', attribute]
    return yaml.safe_load(subprocess.check_output(cmd).decode('UTF-8'))


state_delete = _state_delete
state_get = _state_get
