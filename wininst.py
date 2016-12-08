# Build an installer for Windows

import argparse
import os
import shutil
import sys
import platform

import pip

from nsist import main as pynsist

from gitlabpypi import gitlab_pypi_server


PKGS_DIR = 'pynsist_pkgs'


def test_platform():
    if (sys.platform != 'win32' or platform.machine() != 'AMD64'
            or (sys.version_info.major, sys.version_info.minor) != (3, 5)):
        raise SystemExit('Running on wrong platform/interpreter')


def find_tox_sdist():
    tox_dist_dir = os.path.join('.tox', 'dist')
    sdist, = os.listdir(tox_dist_dir)
    assert sdist.endswith('.zip') or sdist.endswith('.tar.gz')
    return os.path.join(tox_dist_dir, sdist)


def pip_install(*distributions):
    rc = pip.main(['install', '--target={}'.format(PKGS_DIR), *distributions])
    if rc != 0:
        raise SystemExit('pip install failed')


parser = argparse.ArgumentParser(description='Create a Windows installer.')
parser.add_argument('distribution', type=str, nargs='?',
                    help='requirement specifier or distribution archive for '
                         'the rinohtype version to include in the installer')
parser.add_argument('-t', '--use-tox-sdist', action='store_true',
                    help='install the tox-built distribution')
parser.add_argument('-p', '--pro', action='store_true',
                    help='build a Pro version installer (with DITA support)')

if __name__ == '__main__':
    args = parser.parse_args()
    test_platform()
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists(PKGS_DIR):
        shutil.rmtree(PKGS_DIR)
    os.mkdir(PKGS_DIR)
    if args.use_tox_sdist:
        assert args.distribution is None
        rinohtype_dist = find_tox_sdist()
    else:
        assert args.distribution is not None
        rinohtype_dist = args.distribution
    pip_install('pygments', rinohtype_dist)
    if args.pro:
        with gitlab_pypi_server() as index_url:
            pip_install('--extra-index-url', index_url, 'rinoh-frontend-dita')
    pynsist(['wininst.cfg'])
