#!/bin/env python

"""
Setup script for RinohType
"""

import os
import sys

from datetime import datetime
from setuptools import setup, find_packages
from subprocess import Popen, PIPE


PACKAGE = 'rinoh'
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ABSPATH = os.path.join(BASE_PATH, PACKAGE)
VERSION_FILE = os.path.join(PACKAGE_ABSPATH, 'version.py')

# retrieve the version number from git or VERSION_FILE
# inspired by http://dcreager.net/2010/02/10/setuptools-git-version-numbers/
try:
    print('Attempting to get version number from git...')
    git = Popen(['git', 'describe', '--abbrev=4', '--dirty'],
                stdout=PIPE, stderr=sys.stderr)
    if git.wait() != 0:
        raise OSError
    line = git.stdout.readlines()[0]
    __version__ = line.strip()[1:].decode('ascii')
    __release_date__ = datetime.now().strftime('%b %d %Y, %H:%M:%S')
    with open(VERSION_FILE, 'w') as version_file:
        version_file.write("__version__ = '{}'\n".format(__version__))
        version_file.write("__release_date__ = '{}'\n".format(__release_date__))
except OSError as e:
    print('Assume we are running from a source distribution.')
    # read version from from VERSION_FILE
    with open(VERSION_FILE) as version_file:
        code = compile(version_file.read(), VERSION_FILE, 'exec')
        exec(code)

def long_description():
    with open(os.path.join(BASE_PATH, 'README.rst')) as readme:
        result = readme.read()
    result += '\n\n'
    with open(os.path.join(BASE_PATH, 'CHANGES.rst')) as changes:
        result += changes.read()
    return result


setup(
    name='RinohType',
    version=__version__,
    packages=find_packages(),
    package_data={PACKAGE: ['data/fonts/adobe14/*.afm',
                            'data/fonts/adobe14/MustRead.html',
                            'data/fonts/adobe35/*.afm',
                            'data/fonts/adobe35/MustRead.html',
                            'data/hyphen/*.dic',
                            'data/xml/catalog',
                            'data/xml/w3c-entities/*.ent',
                            'backend/pdf/xobject/icc/*.icc',
                            'backend/pdf/xobject/icc/*.txt',
                            ]},
    scripts=['bin/rinoh'],
    install_requires=['setuptools', 'pip', 'docutils', 'purepng>=0.1.1'],
    extras_require = {'bitmap':  ['Pillow']},
    #test_suite='nose.collector',

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
