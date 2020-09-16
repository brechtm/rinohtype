
import pytest


@pytest.mark.sphinx(buildername='rinoh', testroot='minimal')
def test_minimal(app, verify):
    app.build()
    verify()


@pytest.mark.sphinx(buildername='rinoh', testroot='subdir')
def test_subdir(app, verify):
    app.build()
    verify()
