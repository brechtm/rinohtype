#!/usr/bin/env python

"""
Setup script for rinohtype
"""

import sys

import pkg_resources

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py


if sys.version_info < (3, 5):
    print('rinohtype requires Python 3.5 or higher')
    sys.exit(1)


def get_version():
    import sys

    from datetime import date
    from subprocess import check_output, CalledProcessError, DEVNULL

    VERSION = '0.4.1'

    try:
        is_dirty = check_output(['git', 'status', '--porcelain'],
                                stderr=DEVNULL).decode('utf-8')
    except CalledProcessError:
        is_dirty = None   # not running from a git checkout

    if len(sys.argv) > 1 and sys.argv[1] == 'develop':
        # 'pip install -e' or 'python setup.py develop'
        print('Installing in develop mode')
        version = 'dev'
    elif VERSION.endswith('.dev'):  # development distribution
        if is_dirty is None:
            version = version_from_pkginfo() or VERSION
        else:
            print('Attempting to get commit SHA1 from git...')
            git_sha1 = check_output(['git', 'rev-parse', '--short', 'HEAD'])
            version = '{}+{}'.format(VERSION, git_sha1.strip().decode('ascii'))
            if is_dirty:
                version += '.dirty{}'.format(date.today().strftime('%Y%m%d'))
    else:  # release distribution
        if is_dirty is None:
            assert version_from_pkginfo() in (VERSION, None)
        elif is_dirty:
            print(is_dirty)
            assert False
        version = VERSION
    return pkg_resources.safe_version(version)


def version_from_pkginfo():
    from email.parser import HeaderParser

    parser = HeaderParser()
    try:
        with open('PKG-INFO') as file:
            pkg_info = parser.parse(file)
    except FileNotFoundError:
        print('This is not a regular source distribution!')
        return None
    print('Retrieving the distribution version from PKG-SOURCES.')
    return pkg_info['Version']


def long_description():
    import os

    base_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_path, 'README.rst')) as readme:
        result = readme.read()
    result += '\n\n'
    with open(os.path.join(base_path, 'CHANGES.rst')) as changes:
        result += changes.read()
    return result


class BuildPyCommand(build_py):
    """Write the distribution version to rinoh/version.py"""

    def run(self):
        build_py.run(self)
        self.execute(self.set_version, (self.distribution.get_version(), ),
                     "writing the distribution version to rinoh/version.py")

    def set_version(self, version):
        ver = self.get_module_outfile(self.build_lib, ('rinoh', ), 'version')
        with open(ver, 'r') as version_old:
            contents = version_old.readlines()
        with open(ver, 'w') as version_new:
            for line in contents:
                if line.startswith('__version__'):
                    line = "__version__ = '{}'\n".format(version)
                version_new.write(line)


setup(
    cmdclass={'build_py': BuildPyCommand},
    name='rinohtype',
    version=get_version(),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    python_requires='>= 3.5',
    install_requires=['setuptools', 'pip', 'docutils', 'recommonmark',
                      'rinoh-typeface-texgyrecursor>=0.1.1',
                      'rinoh-typeface-texgyreheros>=0.1.1',
                      'rinoh-typeface-texgyrepagella>=0.1.1',
                      'rinoh-typeface-dejavuserif'],
    extras_require = {'bitmap':  ['Pillow']},
    entry_points={
        'console_scripts': [
            'rinoh = rinoh.__main__:main',
        ],
        'rinoh.frontends': [
            'CommonMark = rinoh.frontend.commonmark:CommonMarkReader',
            'reStructuredText = rinoh.frontend.rst:ReStructuredTextReader',
        ],
        'rinoh.templates': [
            'article = rinoh.templates:Article',
            'book = rinoh.templates:Book',
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
        ],
        'sphinx.builders': [
            'rinoh = rinoh.frontend.sphinx',
        ],
    },
    tests_require=['pytest>=2.0.0', 'pytest-assume'],

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
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Printing',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Fonts',
        'Topic :: Text Processing :: Markup',
        'Topic :: Text Processing :: Markup :: XML'
    ]
)
