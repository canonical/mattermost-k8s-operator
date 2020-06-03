# Copied from interface-pgsql/pgsql/pgsql.py

import subprocess
import yaml

from typing import Dict


def _leader_get(attribute: str):
    cmd = ['leader-get', '--format=yaml', attribute]
    return yaml.safe_load(subprocess.check_output(cmd).decode('UTF-8'))


def _leader_set(settings: Dict[str, str]):
    cmd = ['leader-set'] + ['{}={}'.format(k, v or '') for k, v in settings.items()]
    subprocess.check_call(cmd)


leader_get = _leader_get
leader_set = _leader_set
