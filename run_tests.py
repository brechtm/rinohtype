# usage:
#   run_tests.py [PYTEST_ARGS]

import os
import subprocess
import sys


SHELL = sys.platform == 'win32'


if __name__ == '__main__':
    command = ['py.test']
    if os.environ.get('WITH_COVERAGE') == '1':
        command.extend(['--cov=rinoh', '--cov-report=xml'])
    command.extend(sys.argv[1:])
    rc = subprocess.call(command, shell=SHELL)
    raise SystemExit(rc)
