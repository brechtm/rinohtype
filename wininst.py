# Build an installer for Windows

import os
import shutil
import sys
import platform

import pip

from nsist import main as pynsist


PKGS_DIR = 'pynsist_pkgs'


def test_platform():
    if (sys.platform != 'win32' or platform.machine() != 'AMD64'
            or (sys.version_info.major, sys.version_info.minor) != (3, 5)):
        raise SystemExit('Running on wrong platform/interpreter')


def install_package(distribution_name):
    pip.main(['install', '--target={}'.format(PKGS_DIR), distribution_name])



if __name__ == '__main__':
    test_platform()
    shutil.rmtree('build')
    shutil.rmtree(PKGS_DIR)
    os.mkdir(PKGS_DIR)
    install_package('rinohtype')
    install_package('pygments')
    pynsist(['wininst.cfg'])
