Developing
==========

This project makes use of Nox_ to manage running tests and other tasks. The
tests can be divided into three categories: checks, unit tests and regression
(integration) tests. ``noxfile.py`` defines "sessions" that configure these
tasks. Each of these are described in the next section. The unit and regression
tests make use of pytest_.

The repository includes a Poetry_ ``pyproject.toml`` file to help you set up a
virtual environment with Nox and other development dependencies. From the
repository checkout root directory execute::

    poetry install

Poetry will create a virtual environment in *.venv*, which you can activate
like this (on Linux/macOS)::

    source .venv/bin/activate

Now Nox is available for running the tests. Alternatively, you can run Nox
through Poetry::

    poetry run nox

Starting ``nox`` without any arguments will run the *check*, *check_docs*,
*unit* and *regression* sessions. Refer to the next section for an overview of
all sessions.

.. _Nox: https://nox.thea.codes
.. _pytest: https://www.pytest.org
.. _Poetry: https://python-poetry.org/
.. _direnv: https://direnv.net/


Nox Sessions
------------

The following sessions execute unit tests and regression tests:

``unit``
    Runs the unit tests.

``regression``
    Runs integration/regression tests. Each of these tests render a tiny
    document (often a single page) focusing on a specific feature, which means
    they also execute quickly. Their PDF output is compared to a reference PDF
    that is known to be good. This requires ImageMagick and either MuPDF's
    *mutool* or poppler's *pdftoppm* to be available from the search path.

These sessions are parametrized_ in order to run the tests against both the
source and wheel distributions, and against all supported Python versions.
Executing e.g. ``nox --session unit`` will run all of these combinations. Run
``nox --list`` to display these. You can run a single session like this:
``nox --session "<session name>"``.

``unit_sphinx``, ``regression_docutils``, ``regression_sphinx``
    These are variations on the *unit* and *regression* sessions that run the
    (relevant) tests against several versions of the principal rinohtype
    dependencies, docutils and Sphinx (respecting version constraints specified
    in ``pyproject.toml``).

Note that for development purposes, it generally suffices to run the default
set of sessions. `Continuous integration`_ will run all session to catch
regressions.

The other environments run checks, build documentation and build "binary"
distributions for Mac and Windows:

``check``
    Performs basic checks; just ``poetry check`` at this point.

``check_docs``
    Perform checks on the documentation source files using doc8_ and
    sphinx-doctest_. restview_ can be useful when fixing syntax errors in
    ``README.rst``, ``CHANGES.rst``, ...

``build_docs``
    Build the rinohtype documentation using Sphinx, both in HTML and PDF
    formats.

``macapp`` (not maintained, broken?)
    Build a stand-alone macOS application bundle using briefcase_. This task
    can only be run on macOS.

``wininst`` (not maintained, broken?)
    Build a stand-alone rinohtype installer for the Windows platform with the
    help of pynsist_. This task also can be run on other platforms than
    Windows.

Customization settings for doc8_ and pytest_ are stored in ``setup.cfg``.

.. _parametrized: https://nox.thea.codes/en/stable/config.html?highlight=run#parametrizing-sessions
.. _distutils: https://docs.python.org/3/distutils/examples.html#checking-a-package
.. _doc8: https://github.com/PyCQA/doc8
.. _sphinx-doctest: https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html
.. _restview: https://mg.pov.lt/restview/
.. _briefcase: https://beeware.org/briefcase/
.. _pynsist: https://pynsist.readthedocs.io/en/latest/


Testing against multiple Python interpreter versions
----------------------------------------------------

Nox facilitates running tests on multiple Python interpreter versions. You can
combine the ``unit`` and ``regression`` sessions with a Python `version
number`_ to execute it on a specific Python interpreter version. For example,
to run the unit tests with CPython 3.8::

    nox -e unit-3.8

While it is typically sufficient to test on a single Python version during
development, it can be useful to run tests on a set of Python versions before
pushing your commits. Of course, this requires these versions to be available
on your machine. It is highly recommended you use pyenv_ (or pyenv-win_) to
install and manage these. For example, to install CPython 3.8.1, you can run::

    pyenv install 3.8.1

and pyenv will download, build and install this version of CPython for you.
pyenv will install the different Python versions in an isolated location
(typically under ``~/.penv``), so they will not interfere with your
system-default Python versions.

The file ``.python-version`` in the root of the repository specifies which
Python versions pyenv should make available whenever we are inside the
repository checkout directory. The file lists specific the versions of CPython
rinohtype aims to support plus recent PyPy3 versions (ideally, we should
closely track the latest releases). The ``pyenv_install.py`` script can install
these for you (skipping any that are already installed).

.. _version number: https://nox.thea.codes/en/stable/tutorial.html#testing-against-different-and-multiple-pythons
.. _pyenv: https://github.com/pyenv/pyenv
.. _pyenv-win: https://github.com/pyenv-win/pyenv-win


Continuous integration
----------------------

`GitHub Actions`_ automatically executes the Nox sessions when new commits
are pushed to the repository. The Nox sessions are run on Linux, macOS and
Windows, and run the tests against an array of Python, docutils and Sphinx
versions to make sure that we don't break any corner cases. See
``.github/workflows`` for details.

.. _GitHub Actions: https://github.com/brechtm/rinohtype/actions


Making a release
----------------

This is a list of steps to follow when making a new release of rinohtype.
Publishing the new release to PyPI_ and uploading the documentation to GitHub
Pages is handled by the GitHub Actions workflow.

1. Make sure your checkout is clean.

2. Update dependencies::

    poetry show --outdated
    poetry update

3. Run basic tests and checks locally::

    nox

4. Push your commits to master on GitHub. Don't create a tag yet!

5. Check whether all tests on `GitHub Actions`_ are green.

6. Set the release date.

   * set ``__release_date__`` in *src/rinoh/__init__.py* (``YYYY-MM-DD``)
   * add release date to this release's section (see other sections for
     examples)

7. Create a git tag: ``git tag v$(poetry version --short)``

8. Push the new tag: ``git push origin v$(poetry version --short)``

9. The GitHub workflow will run all Nox sessions and upload the new version
   to PyPI if all checks were successful.

10. Create a `new release on GitHub`_. Include the relevant section of the
    changelog. Use previous releases as a template.

    * Tag version: the release's tag *vx.y.z*
    * Release title: *Release x.y.z (date)*
    * Add a link to the release on PyPI::

          Install from [PyPI](https://pypi.org/project/rinohtype/x.y.z/)

    * Copy the release notes from the change log

11. Bump version number and reset the release date to "upcoming".

    * ``poetry version patch  # or 'minor'``
    * add new section at the top of the changelog
    * set ``__release_date__`` in *src/rinoh/__init__.py* to ``'upcoming'``


.. _PyPI: https://pypi.org/
.. _new release on GitHub: https://github.com/brechtm/rinohtype/releases/new
