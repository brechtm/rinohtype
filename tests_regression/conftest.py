
import os

from pathlib import Path

import pytest
import sphinx


from .helpers.regression import verify_output


ROOT_DIR = Path(__file__).parent / 'sphinx'


pytest_plugins = 'sphinx.testing.fixtures'
collect_ignore = ['sphinx']


@pytest.fixture(scope='session')
def rootdir():
    if sphinx.version_info < (8, 0):
        from sphinx.testing.path import path
        return path(__file__).parent.abspath() / 'sphinx'
    else:
        return Path(__file__).parent / 'sphinx'


@pytest.fixture(scope='function')
def verify(app, rootdir):
    def _verify():
        testroot = app.srcdir.basename()
        verify_output(testroot, app.outdir, rootdir)
    return _verify


@pytest.fixture(scope="session", autouse=True)
def disable_cache():
    old_environ = dict(os.environ)
    os.environ['RINOH_NO_CACHE'] = '1'
    yield
    os.environ.update(old_environ)
