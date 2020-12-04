
import pytest


@pytest.mark.sphinx(buildername='rinoh', testroot='minimal')
def test_minimal(app, verify):
    app.build()
    verify()


@pytest.mark.sphinx(buildername='rinoh', testroot='subdir')
def test_subdir(app, verify):
    app.build()
    verify()


@pytest.mark.sphinx(buildername='rinoh', testroot='relativepaths')
def test_relativepaths(app, verify):
    app.build()
    verify()


@pytest.mark.sphinx(buildername='rinoh', testroot='outoflineflowables')
def test_outoflineflowables(app, verify):
    app.build()
    verify()
