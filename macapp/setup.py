#!/usr/bin/env python

"""
Setup script for a stand-alone rinoh macOS application bundle
"""


import os

from setuptools import setup, find_packages


setup(
    name=os.environ['MACAPP_NAME'],
    version=os.environ['MACAPP_VERSION'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={'rinoh_macapp': ['rinoh.sh']}
)
