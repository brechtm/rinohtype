Developing
==========

This project makes use of tox_ to manage running tests and other tasks. The
tests can be divided into three categories: checks, unit tests and regression
tests. ``tox.ini`` defines "environments" that configure these tasks. Each of
these are described below. The unit and integration tests make use of the
pytest_ framework.

Tox facilitates running tests on multiple Python interpreter versions. This
requires these versions to be available on your machine. We recommend you use
pyenv_ (or pyenv-win_) to manage the installation of different Python
interpreters.

.. _tox: https://tox.readthedocs.io
.. _pytest: https://www.pytest.org
.. _pyenv: https://github.com/pyenv/pyenv
.. _pyenv-win: https://github.com/pyenv-win/pyenv-win


Environments
------------

``py35``, ``py36``, ``py37``, ``py38``, ``py39``, ``pypy3``
    Runs the unit tests in the interpreter corresponding to the name of the
    environment.

``check``
    Performs various checks using distutils_ and check-manifest_ to see whether

    - the package's meta-data is not missing any parts,
    - the package's long description is valid reStructuredText, and
    - we didn't forget to include any files in the source distribution

``regression``
    Runs "unit-like" regression tests that finish in a short amount of time.
    These tests render small documents whose PDF output is compared to a
    reference PDF.

``longrunning``
    Runs regressions tests that render larger documents. These tests take
    several minutes to complete.

``check-docs``
    Perform checks on the documentation source files using doc8_ and
    sphinx-doctest_.

``build-docs``
    Build the rinohtype documentation using Sphinx, both in HTML and PDF
    formats.

``macapp``
    Build a stand-alone macOS application bundle using briefcase_. This task
    can only be run on macOS.

``wininst``
    Build a stand-alone rinohtype installer for the Windows platform with the
    help of pynsist_. This task also can be run on other platforms than
    Windows.

Customization settings for check-manifest_, doc8_ and pytest_ are stored in
``setup.cfg``.


.. _distutils: https://docs.python.org/3/distutils/examples.html#checking-a-package
.. _check-manifest: https://github.com/mgedmin/check-manifest
.. _doc8: https://github.com/PyCQA/doc8
.. _sphinx-doctest: https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html
.. _briefcase: https://beeware.org/briefcase/
.. _pynsist: https://pynsist.readthedocs.io/en/latest/


Managing multiple Python interpreter versions
---------------------------------------------

To be able to test rinohtype against multiple Python interpreter versions,
these need to be available on your machine. pyenv_ can help you easily manage
these. For example, to install CPython 3.8.1, you can run

::

    pyenv install 3.8.1

and pyenv will download, build and install this version of CPython for you.

Note that pyenv will install the different Python versions in an isolated
location (typically under ``~/.penv``), so they will not interfere with your
system-default Python versions.

The file ``.python-version`` in the root of the repository specifies which
Python versions pyenv should make available whenever we are inside the
repository. The file lists specific versions of CPython 3.5 to 3.9 and a
recent PyPy3 version (Ideally, we should closely track the latest releases).
The ``pyenv_install.py`` script will install the interpreters listed in
``.python-version`` for you.

In addition to these versions, the first entry of the ``.python-version``
specifies ``rinoh-tox``. This is a virtual environment that has tox installed
along with some other tools required for making a new rinohtype release. The
``pyenv_install.py`` script instructs you how to set up this virtual
environment. This requires pyenv-virtualenv_, a pyenv plugin.

.. _pyenv-virtualenv: https://github.com/pyenv/pyenv-virtualenv


Executing tox environments
--------------------------

With all this in place, you can now run tox to execute the environments.
Invoking tox without any options will run all tox environments listed in
``tox.ini``'s ``envlist``. You can specify specific environments by passing
them to the ``-e`` argument::

    tox -e py35,py38        # no spaces!

For each environment, tox will create virtual environments (under ``.tox``) and
install rinohtype (from sdist) in these. Additionally, it will install other
dependencies specified by ``tox.ini`` before running tests.

.. _pyenv-virtualenv: https://github.com/pyenv/pyenv-virtualenv


Continuous Integration
----------------------

We make use of Travis CI and AppVeyor to automatically execute the tox
environments when new commits are pushed to the repository. Travis CI covers
the Linux and macOS platforms, while AppVeyor covers Windows. See the
configuration files ``.travis.yml`` and ``appveyor.yml`` for details.


Making a release
----------------

This is a list of steps to follow when making a new release of rinohtype:

1. restview_ ``README.rst`` and ``CHANGES.rst`` to check for issues

2. Make sure the git clone is clean (``git status`` returns nothing)

   * you can ``git stash`` uncommited changes

3. Set release version

   * ``export VERSION_NUMBER=$(bumpversion --list release | grep current_version | sed s/"^.*="//)``
   * change release date in ``rinoh/version.py`` and ``CHANGES.rst``

4. Commit these changes and run all tests

   * ``git commit -am "Bump version to $VERSION_NUMBER"``
   * ``git push``
   * wait for Travis CI and AppVeyor results

5. Remove build and dist directories: ``rm -rf build dist``

6. Build distribution files: ``python setup.py sdist bdist_wheel``

7. Make sure the ``doc/_build/html`` submodule is checked out

8. Build and commit the documentation

   * ``tox --installpkg dist/*.whl -e build-docs``
   * ``git commit -am "$VERSION_NUMBER docs" doc/_build/html``

9. Upload the distribution files to TestPyPI_ using twine_

   * ``twine upload -r testpypi dist/*``
   * check whether the new release's description (which is a concatenation of
     ``README.rst`` and ``CHANGES.rst``) is rendered properly

10. Tag the release in version control

    * ``git tag $VERSION_NUMBER``
    * ``git push --tags``

11. Upload the distribution files to PyPI_ using twine_

    * ``twine upload dist/*``

12. Set the new development version

    * ``export VERSION_NUMBER=$(bumpversion --list patch | grep current_version | sed s/"^.*="//)``
    * set the date in ``version.py`` to 'unreleased'
    * ``git commit -am "Bump version to $VERSION_NUMBER"``


.. _bumpversion: https://pypi.org/project/bumpversion/
.. _restview: https://mg.pov.lt/restview/
.. _twine: https://pypi.org/project/twine/
.. _TestPyPI: https://test.pypi.org/
.. _PyPI: https://pypi.org/
