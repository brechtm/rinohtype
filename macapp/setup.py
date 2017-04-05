#!/usr/bin/env python

"""
Setup script for a stand-alone rinoh macOS application bundle
"""


import os

from pkg_resources import WorkingSet
from setuptools import setup, find_packages


APP_PACKAGES_DIR = os.path.join('macOS', 'rinoh.app', 'Contents',
                                'Resources', 'app_packages')


def get_version():
    working_set = WorkingSet([APP_PACKAGES_DIR])
    return working_set.by_key['rinohtype'].version


setup(
    name=os.environ['MACAPP_NAME'],
    version=get_version(),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={'rinoh_macapp': ['rinoh.sh']}
)
