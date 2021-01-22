#!/usr/bin/env python

import re
import subprocess


def echo_and_run(*args):
    command = ' '.join(args)
    print('  ' + command)
    subprocess.call(args)


versions = []
with open('.python-version') as python_version:
    for line in python_version:
        version = line.strip()
        if version:
            versions.append(version)

for version in versions:
    print('Installing {} using pyenv...'.format(version))
    echo_and_run('pyenv', 'install', '--skip-existing', version)

print("Now you can set up the development virtualenv:")
print('  poetry install')
