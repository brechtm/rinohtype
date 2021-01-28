# Set or update TOXENV envvar based on GitHub Actions' set-python version

import os
import sys

_, github_python_version = sys.argv

mapping = {'3.6':                 'py36',
           '3.7':                 'py37',
           '3.8':                 'py38',
           '3.9':                 'py39',
           '3.10.0-alpha - 3.10': 'py310',
           'pypy-3.6':            'pypy3',
           'pypy-3.7':            'pypy3'}

toxenv = os.getenv('TOXENV')
factor = mapping[github_python_version]
toxenv = f'{toxenv}-{factor}' if toxenv else factor

with open(os.getenv('GITHUB_ENV'), 'a') as env:
    print(f'TOXENV={toxenv}', file=env)
