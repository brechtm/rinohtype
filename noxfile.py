
import glob
import os
import shutil
import sys

import nox
import nox_poetry

sys.path.append('.')
from noxutil import get_versions

CURRENT_PYTHON = (('pypy' if hasattr(sys, 'pypy_version_info') else '')
                  + f'{sys.version_info.major}.{sys.version_info.minor}')

nox.options.sessions = ['check', 'check_docs',
                        f'unit-{CURRENT_PYTHON}(wheel)',
                        f'regression-{CURRENT_PYTHON}(wheel)']


PYTHONS = ['3.8', '3.9', '3.10', '3.11', '3.12', '3.13']
PYTHONS += ['pypy3'] if os.getenv('CI') else ['pypy3.10']

DEPENDENCIES = ['pytest', 'pytest-xdist', 'pytest-cov', 'coverage', 'Sphinx']
if os.getenv('GITHUB_SHA'):
    DEPENDENCIES.append('pytest-github-actions-annotate-failures')


def parametrize_dist():
    return nox.parametrize('dist', ['sdist', 'wheel'], ids=['sdist', 'wheel'])


def parametrize(dependency, granularity='minor', python=CURRENT_PYTHON):
    versions = get_versions(dependency, granularity, python)
    if python != CURRENT_PYTHON:
        for version in get_versions(dependency, granularity, CURRENT_PYTHON):
            versions.remove(version)
    return nox.parametrize(dependency, versions)


# sessions

@nox_poetry.session
def check(session):
    session.run('poetry', 'check', external=True)


@nox_poetry.session
def check_docs(session):
    _install(session, dependencies=['doc8', 'sphinx-immaterial',
                                    'sphinxcontrib-autoprogram'])
    session.run('doc8', 'README.rst', 'CHANGES.rst', 'CONTRIBUTING.rst',
                'DEVELOPING.rst', 'doc')
    session.run('python', 'doc/build.py', 'doctest')


@nox_poetry.session
def build_docs(session):
    _install(session, dependencies=['Sphinx', 'sphinx-immaterial',
                                    'sphinxcontrib-autoprogram'])
    session.chdir('doc')
    session.run('python', 'build.py', *session.posargs)
    # copy 'showcase' directory to the HTML output directory
    shutil.copytree('showcase', '_build/html/showcase', dirs_exist_ok=True)
    # copy PDF docs to the HTML output directory
    for pdf in glob.glob('_build/rinoh/*.pdf'):
        shutil.copy(pdf, '_build/html')



@nox_poetry.session(python=PYTHONS)
@parametrize_dist()
def unit(session, dist):
    _unit(session, dist=dist)


@nox_poetry.session
@parametrize('sphinx')
def unit_sphinx(session, sphinx):
    _unit(session, sphinx=sphinx, ignore_deprecation_warnings=True)


@nox_poetry.session(python='3.9')
@parametrize('sphinx', python='3.9')
def unit_sphinx_py39(session, sphinx):
    _unit(session, sphinx=sphinx, ignore_deprecation_warnings=True)


@nox_poetry.session(python=PYTHONS)
@parametrize_dist()
def regression(session, dist):
    _regression(session, dist=dist)


@nox_poetry.session
@parametrize('docutils')
def regression_docutils(session, docutils):
    _regression(session, docutils=docutils, ignore_deprecation_warnings=True)


@nox_poetry.session
@parametrize('sphinx')
def regression_sphinx(session, sphinx):
    _regression(session, sphinx=sphinx, ignore_deprecation_warnings=True)


@nox_poetry.session(python='3.9')
@parametrize('sphinx', python='3.9')
def regression_sphinx_py39(session, sphinx):
    _regression(session, sphinx=sphinx, ignore_deprecation_warnings=True)


# utility functions

def _install(session, docutils=None, sphinx=None, dist='wheel',
             dependencies=[]):
    session.poetry.installroot(distribution_format=dist)
    if dependencies:
        session.install(*(d for d in dependencies
                          if not (sphinx and d.lower() == 'sphinx')))
    deps = []
    if docutils:
        deps.append(f"docutils=={docutils}")
    if sphinx:
        deps.append(f"sphinx=={sphinx}")
        major, _ = sphinx.split('.', maxsplit=1)
        if int(major) < 4:
            # https://github.com/sphinx-doc/sphinx/issues/10291
            deps.append("jinja2<3.1")
        elif int(major) < 6:
            deps.append("myst-parser==0.18.1")
        if int(major) < 5:
            # https://github.com/sphinx-doc/sphinx/issues/11890
            deps.append("alabaster==0.7.13")
            deps.append("sphinxcontrib-applehelp==1.0.4")
            deps.append("sphinxcontrib-devhelp==1.0.2")
            deps.append("sphinxcontrib-htmlhelp==2.0.1")
            deps.append("sphinxcontrib-serializinghtml==1.1.5")
            deps.append("sphinxcontrib-qthelp==1.0.3")
    if deps:
        session.run("pip", "install", *deps)


def _unit(session, docutils=None, sphinx=None, dist='wheel',
          ignore_deprecation_warnings=False):
    _install(session, docutils=docutils, sphinx=sphinx, dist=dist,
             dependencies=DEPENDENCIES)
    mark_expr = ['-m', 'with_sphinx'] if sphinx else []
    if dist == 'sdist':
        session.env['WITH_COVERAGE'] = '0'
    _run_tests(session, 'tests', *mark_expr,
               ignore_deprecation_warnings=ignore_deprecation_warnings)


def _regression(session, docutils=None, sphinx=None, dist='wheel',
                ignore_deprecation_warnings=False):
    _install(session, docutils=docutils, sphinx=sphinx, dist=dist,
             dependencies=[*DEPENDENCIES, 'defusedxml', # for Sphinx>=7.3
                           'pytest-assume', 'pytest-console-scripts'])
    mark_expr = ['-m', 'with_sphinx'] if sphinx else ['-m', 'not longrunning']
    if dist == 'sdist':
        session.env['WITH_COVERAGE'] = '0'
    _run_tests(session, 'tests_regression', *mark_expr,
               '--script-launch-mode=subprocess',
               ignore_deprecation_warnings=ignore_deprecation_warnings)

    
def _run_tests(session, tests_dir, *args, ignore_deprecation_warnings=False):
    filterwarnings = ['-W', ''] if ignore_deprecation_warnings else []
    session.run('python', 'run_tests.py', *args, *filterwarnings,
                *session.posargs, tests_dir)


# currently unmaintained sessions

@nox_poetry.session(python='python3.7')
def macapp(session):
    session.run('python', 'macapp.py', '--use-tox-sdist')


@nox_poetry.session(python='python3.6')
def wininst(session):
    session.env['SPHINXOPTS'] = '"-Dhtml_theme=bizstyle"'
    session.run('python', 'doc/build.py', 'rinoh', 'htmlhelp')
    session.run('python', 'wininst.py', '--use-tox-sdist')
