# Set NOXPY env var based on GitHub Actions' set-python version

import os
import sys

_, github_python_version = sys.argv

mapping = {'3.10':                '3.10',
           '3.11':                '3.11',
           '3.12':                '3.12',
           '3.13':                '3.13',
           '3.14':                '3.14',
           '3.15.0-alpha - 3.15': '3.15',
           'pypy-3.11':           'pypy3'}

noxenv = os.getenv('NOXENV')
pyfactor = mapping[github_python_version]

if noxenv in ('unit', 'regression'):
    with open(os.getenv('GITHUB_ENV'), 'a') as env:
        print(f'NOXENV={noxenv}-{pyfactor}', file=env)
