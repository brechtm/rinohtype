
import pytest

from sphinx.testing.path import path


from helpers.regression import verify_output


pytest_plugins = 'sphinx.testing.fixtures'
collect_ignore = ['roots']


@pytest.fixture(scope='session')
def rootdir():
    return path(__file__).parent.abspath() / 'roots'


@pytest.fixture(scope='function')
def verify(app, rootdir):
    def _verify():
        testroot = app.srcdir.basename()
        verify_output(testroot, app.outdir, rootdir)

    return _verify


def pytest_configure(config):
    config.addinivalue_line('markers', 'sphinx')
