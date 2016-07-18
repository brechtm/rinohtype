#!/bin/env python

"""
Setup script for RinohType
"""

import os
import re
import sys

from datetime import datetime
from setuptools import setup, find_packages
from subprocess import Popen, PIPE


PACKAGE = 'rinoh'
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ABSPATH = os.path.join(BASE_PATH, PACKAGE)
VERSION_FILE = os.path.join(PACKAGE_ABSPATH, 'version.py')

VERSION_FORMAT = re.compile(r'v\d+\.\d+\.\d+')

# All external commands are relative to BASE_PATH
os.chdir(BASE_PATH)

def get_version():
    # retrieve the version number from git or VERSION_FILE
    # inspired by http://dcreager.net/2010/02/10/setuptools-git-version-numbers/
    try:
        print('Attempting to get version number from git...')
        git = Popen(['git', 'describe', '--always', '--dirty'],
                    stdout=PIPE, stderr=sys.stderr)
        if git.wait() != 0:
            raise OSError
        line, = git.stdout.readlines()
        line = line.strip().decode('ascii')
        version = line[1:] if VERSION_FORMAT.match(line) else line
        release_date = datetime.now().strftime('%b %d %Y, %H:%M:%S')
    except OSError as e:
        print('Assume we are running from a source distribution.')
        # read version from VERSION_FILE
        with open(VERSION_FILE) as version_file:
            code = compile(version_file.read(), VERSION_FILE, 'exec')
        exec(code)
        version = locals()['__version__']
        release_date = locals()['__release_date__']
    return version, release_date


if sys.argv[1] == 'develop':   # 'pip install -e' or 'python setup.py develop'
    print('Installing in develop mode')
    version, release_date = 'dev', 'now'
else:
    version, release_date = get_version()

with open(VERSION_FILE, 'w') as version_file:
    version_file.write("__version__ = '{}'\n".format(version))
    version_file.write("__release_date__ = '{}'\n".format(release_date))


def long_description():
    with open(os.path.join(BASE_PATH, 'README.rst')) as readme:
        result = readme.read()
    result += '\n\n'
    with open(os.path.join(BASE_PATH, 'CHANGES.rst')) as changes:
        result += changes.read()
    return result


setup(
    name='RinohType',
    version=version,
    packages=find_packages(),
    package_data={PACKAGE: ['data/fonts/adobe14/*.afm',
                            'data/fonts/adobe14/MustRead.html',
                            'data/fonts/zapfdingbats.txt',
                            'data/hyphen/*.dic',
                            'data/stylesheets/*.rts',
                            'data/xml/catalog',
                            'data/xml/w3c-entities/*.ent',
                            'backend/pdf/xobject/icc/*.icc',
                            'backend/pdf/xobject/icc/*.txt',
                            ]},
    install_requires=['setuptools', 'pip', 'docutils', 'purepng>=0.1.1'],
    extras_require = {'bitmap':  ['Pillow']},
    entry_points={
        'console_scripts': [
            'rinoh = rinoh.tool:main',
        ],
        'rinoh.stylesheets': [
            'sphinx = rinoh.stylesheets:sphinx',
            'sphinx_article = rinoh.stylesheets:sphinx_article',
            'sphinx_base14 = rinoh.stylesheets:sphinx_base14',
        ],
        'rinoh.typefaces': [
            'courier = rinoh.fonts.adobe14:courier',
            'helvetica = rinoh.fonts.adobe14:helvetica',
            'symbol = rinoh.fonts.adobe14:symbol',
            'times = rinoh.fonts.adobe14:times',
            'itc zapfdingbats = rinoh.fonts.adobe14:zapfdingbats',
        ]
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest>=2.0.0', 'pytest-assume', 'requests', 'PyPDF2'],

    author='Brecht Machiels',
    author_email='brecht@mos6581.org',
    description='The Python document processor',
    long_description=long_description(),
    url='https://github.com/brechtm/rinohtype',
    keywords='rst xml pdf opentype',
    classifiers = [
        'Environment :: Console',
        'Environment :: Other Environment',
        'Environment :: Web Environment',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Printing',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Fonts',
        'Topic :: Text Processing :: Markup',
        'Topic :: Text Processing :: Markup :: XML'
    ]
)
