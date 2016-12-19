#!/usr/bin/env python

"""
Setup script for rinohtype
"""

import sys

from setuptools import setup, find_packages


if sys.version_info < (3, 3):
    print('rinohtype requires Python 3.3 or higher')
    sys.exit(1)


def long_description():
    import os

    base_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_path, 'README.rst')) as readme:
        result = readme.read()
    result += '\n\n'
    with open(os.path.join(base_path, 'CHANGES.rst')) as changes:
        result += changes.read()
    return result


setup(
    name='rinohtype',
    version='0.3.1',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    python_requires='>= 3.3',
    install_requires=['setuptools', 'pip', 'docutils', 'purepng>=0.2.0',
                      'recommonmark',
                      'rinoh-typeface-texgyrecursor>=0.1.1',
                      'rinoh-typeface-texgyreheros>=0.1.1',
                      'rinoh-typeface-texgyrepagella>=0.1.1',
                      'rinoh-typeface-dejavuserif'],
    extras_require = {'bitmap':  ['Pillow']},
    entry_points={
        'console_scripts': [
            'rinoh = rinoh.tool:main',
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
        ]
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Printing',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Fonts',
        'Topic :: Text Processing :: Markup',
        'Topic :: Text Processing :: Markup :: XML'
    ]
)
