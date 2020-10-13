# usage:
#   run_tests.py [PYTEST_ARGS]

import os
import subprocess
import sys

from coverage import Coverage


SHELL = sys.platform == 'win32'


if __name__ == '__main__':
    command = ['py.test', '-n', 'auto']
    if os.environ.get('WITH_COVERAGE') == '1':
        command.extend(['--cov=rinoh', '--cov-report='])
    if os.environ.get('BASETEMP'):
        command.append('--basetemp={}'.format(os.environ['BASETEMP']))
    command.extend(sys.argv[1:])
    rc = subprocess.call(command, shell=SHELL)
    if os.environ.get('WITH_COVERAGE') == '1':
        cov = Coverage()
        cov.load()
        cov.combine()
        cov.report(skip_covered=True)
        cov.xml_report()
    raise SystemExit(rc)
