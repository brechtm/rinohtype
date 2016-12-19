# Build an application bundle for macOS

import argparse
import os
import re
import shutil
import subprocess

from setuptools import setup

from gitlabpypi import gitlab_pypi_server


APP_VERSION = '0.3.1'

TOX_DIST_DIR = os.path.join('.tox', 'dist')


def find_tox_sdist():
    sdist, = os.listdir(TOX_DIST_DIR)
    assert sdist.endswith('.zip') or sdist.endswith('.tar.gz')
    return os.path.join(TOX_DIST_DIR, sdist)


def create_app(name, version, requirements):
    os.environ['MACAPP_NAME'] = name
    version = os.environ['MACAPP_VERSION'] = version
    os.chdir('macapp')
    setup(
        name='rinoh_macapp',
        version=version,
        options = {
            'app': {
                'formal_name': 'rinoh',
                'bundle': 'com.opqode.rinoh'
            },
            'macos': {
                'icon': '../icons/rinoh'
            },
        },
        install_requires=requirements,
        setup_requires=['briefcase'],
        script_name='setup.py',
        script_args=['macos']
    )


parser = argparse.ArgumentParser(description='Create a macOS application.')
parser.add_argument('distribution', type=str, nargs='?',
                    help='requirement specifier or distribution archive for '
                         'the rinohtype version to include in the installer')
parser.add_argument('-t', '--use-tox-sdist', action='store_true',
                    help='install the tox-built distribution')
parser.add_argument('-p', '--pro', action='store_true',
                    help='build a Pro version installer (with DITA support)')


APP_DIR = os.path.join('macapp', 'macOS')


RE_SDIST_VERSION = re.compile(r'^rinohtype-'
                              r'(?P<version>\d+\.\d+\.\d+(\.dev\d+)?)\.zip$')


if __name__ == '__main__':
    args = parser.parse_args()
    if os.path.exists(APP_DIR):
        shutil.rmtree(APP_DIR)
    if args.use_tox_sdist:
        assert args.distribution is None

        # Work around a problem with pip wheel caching
        # (https://github.com/pypa/pip/issues/4183)
        os.environ['PIP_NO_CACHE_DIR'] = '0'

        os.environ['PIP_FIND_LINKS'] = os.path.abspath(TOX_DIST_DIR)
        _, sdist_filename = os.path.split(find_tox_sdist())
        m = RE_SDIST_VERSION.match(sdist_filename)
        rinohtype_dist = 'rinohtype=={}'.format(m.group('version'))
    else:
        assert args.distribution is not None
        rinohtype_dist = args.distribution
    requirements = ['pygments', rinohtype_dist]
    if args.pro:
        requirements.append('rinoh-frontend-dita')
        with gitlab_pypi_server() as index_url:
            os.environ['PIP_EXTRA_INDEX_URL'] = index_url
            app_name = 'rinoh pro'
            create_app(app_name, APP_VERSION, requirements)
    else:
        app_name = 'rinoh'
        create_app(app_name, APP_VERSION, requirements)
    print('Creating disk image...')
    dmg_filename = '{}-{}.dmg'.format(app_name.replace(' ', '_'), APP_VERSION)
    subprocess.call(['hdiutil', 'create', '-ov', '-srcfolder', 'macOS',
                     '-volname', app_name, '../dist/{}'.format(dmg_filename)])
