# Based on interface-pgsql/pgsql/pgsql.py

import subprocess
import yaml

from typing import Dict


def _state_get(attribute: str):
    cmd = ['state-get', '--format=yaml', attribute]
    return yaml.safe_load(subprocess.check_output(cmd).decode('UTF-8'))


def _state_set(settings: Dict[str, str]):
    cmd = ['state-set'] + ['{}={}'.format(k, v or '') for k, v in settings.items()]
    subprocess.check_call(cmd)


state_get = _state_get
state_set = _state_set