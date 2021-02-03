Developing
==========

This project makes use of tox_ to manage running tests and other tasks. The
tests can be divided into three categories: checks, unit tests and regression
(integration) tests. ``tox.ini`` defines "environments" that configure these
tasks. Each of these are described in the next section. The unit and regression
tests make use of pytest_.

The repository includes a Poetry_ ``pyproject.toml`` file to help you set up a
virtual environment with tox and other development dependencies. From the
repository checkout root directory execute::

    poetry install

Poetry will create a virtual environment in *.venv*, which you can activate
like this\ [#]_::

    source .venv/bin/activate

Now tox is available for running the tests. Starting ``tox`` without any
arguments will run the *check*, *unit* and *regression* environments. Refer to
the next section for an overview of all environments.

.. [#] If you install direnv_, the virtual environment can be automatically
       activated when you enter the rinohtype repository checkout (see the
       ``.envrc`` file).

.. _tox: https://tox.readthedocs.io
.. _pytest: https://www.pytest.org
.. _Poetry: https://python-poetry.org/
.. _direnv: https://direnv.net/


Tox Environments
----------------

The following environments execute unit tests and regression tests:

``unit``
    Runs the unit tests.

``regression``
    Runs integration/regression tests. Each of these tests render a tiny
    document (often a single page) focusing on a specific feature, which means
    they also execute quickly. Their PDF output is compared to a reference PDF
    that is known to be good.

``longrunning`` (not maintained, broken)
    Runs regressions tests that render larger documents. These tests take
    several minutes to complete.

The other environments run checks, build documentation and build "binary"
distributions for Mac and Windows:

``check``
    Performs basic checks; just ``poetry check`` at this point.

``check-docs``
    Perform checks on the documentation source files using doc8_ and
    sphinx-doctest_. restview_ can be useful when fixing syntax errors in
    ``README.rst``, ``CHANGES.rst``, ...

``build-docs``
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


.. _distutils: https://docs.python.org/3/distutils/examples.html#checking-a-package
.. _doc8: https://github.com/PyCQA/doc8
.. _sphinx-doctest: https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html
.. _restview: https://mg.pov.lt/restview/
.. _briefcase: https://beeware.org/briefcase/
.. _pynsist: https://pynsist.readthedocs.io/en/latest/


Testing against multiple Python interpreter versions
----------------------------------------------------

Tox facilitates running tests on multiple Python interpreter versions. You can
combine the test environment names with a factor_ to execute them on a specific
Python interpreter version. For example, to run the unit tests on CPython 3.8::

    tox -e unit-py38

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

.. _factor: https://tox.readthedocs.io/en/latest/config.html#tox-environments
.. _pyenv: https://github.com/pyenv/pyenv
.. _pyenv-win: https://github.com/pyenv-win/pyenv-win


Continuous integration
----------------------

`GitHub Actions`_ automatically executes the tox environments when new commits
are pushed to the repository. The tox environments are run on Linux, macOS and
Windows, and run the tests on an array of Python versions to make sure that we
don't break any corner cases. See ``.github/workflows`` for details.

.. _GitHub Actions: https://github.com/brechtm/rinohtype/actions


Making a release
----------------

This is a list of steps to follow when making a new release of rinohtype.
Publishing the new release to PyPI_ and uploading the documentation to GitHub
Pages is handled by the GitHub Actions workflow.

1. Make sure your checkout is clean.

2. Run run tests and checks locally::

    tox -e check,check-docs,build-docs,unit,regression

3. Push your commits to master on GitHub. Don't create a tag yet!

4. Check whether all tests on `GitHub Actions`_ are green.

5. Set the release date.

   * set ``__release_date__`` in *src/rinoh/__init__.py* (``YYYY-MM-DD``)
   * add release date to this release's section (see other sections for
     examples)

6. Create a git tag: ``git tag v$(poetry version --short)``

7. Push the new tag: ``git push origin v$(poetry version --short)``

8. The GitHub workflow will run all tox environments and upload the new version
   to PyPI if all checks were successful.

9. Create a `new release on GitHub`_. Include the relevant section of the
   changelog. Use previous releases as a template.

   * Tag version: the release's tag *vx.y.z*
   * Release title: *Release x.y.z (date)*
   * Add a link to the release on PyPI::

          Install from [PyPI](https://pypi.org/project/rinohtype/x.y.z/)

   * Copy the release notes from the change log

10. Bump version number and reset the release date to "upcoming".

    * ``poetry version patch  # or 'minor'``
    * add new section at the top of the changelog
    * set ``__release_date__`` in *src/rinoh/__init__.py* to ``'upcoming'``


.. _PyPI: https://pypi.org/
.. _new release on GitHub: https://github.com/brechtm/rinohtype/releases/new
