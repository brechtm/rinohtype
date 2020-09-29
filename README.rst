rinohtype
=========

.. image:: http://img.shields.io/pypi/v/rinohtype.svg
   :target: https://pypi.python.org/pypi/rinohtype
   :alt: PyPI

.. image:: https://img.shields.io/pypi/pyversions/rinohtype.svg
   :target: https://pypi.python.org/pypi/rinohtype
   :alt: Python version

.. image:: https://badges.gitter.im/brechtm/rinohtype.svg
   :target: https://gitter.im/brechtm/rinohtype
   :alt: Gitter chat

.. image:: https://github.com/brechtm/rinohtype/workflows/Tests/badge.svg?branch=master&event=push
   :target: https://github.com/brechtm/rinohtype/actions?query=workflow%3ATests+branch%3Amaster+event%3Apush
   :alt: Tests

.. image:: https://codecov.io/gh/brechtm/rinohtype/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/brechtm/rinohtype
   :alt: Test coverage


rinohtype is a batch-mode document processor. It renders structured documents
to PDF based on a document template and a style sheet. An important design goal
of rinohtype is make document layout and style customization user-friendly. See
the documentation_ to learn how to customize the style of your document.


Call for Contributions
----------------------

Since rinohtype is a fairly sizable project and currently being maintained by a
single person, your contribution can make a big difference. Specifically, the
following things can help move rinohtype forward:

* development of professional-looking stylesheets and document templates
* volunteering to be a maintainer: fix issues that pop up when new versions of
  dependencies are released (Python, Sphinx, ...)
* help with maintaining and improving the documentation
* development of new features, e.g. widow/orphan handling, Knuth-Plass line
  breaking, mathematics typesetting, performance improvements, ...
* companies might be interested in funding the development of particular
  features that would benefit them

So if you are interested in helping with any of these items, please don't
hesitate to get in touch via brecht@opqode.com, `GitHub issues`_ or Gitter_!

.. _GitHub issues: https://github.com/brechtm/rinohtype/issues
.. _Gitter: https://gitter.im/brechtm/rinohtype


Features
--------

rinohtype is still in beta, so you might run into some issues when using it.
I'd highly appreciate it if you could `create a ticket`_ for any bugs you may
encounter. That said, rinohtype is already quite capable. For example, it
should be able to replace Sphinx_'s LaTeX builder in most cases. Here is an
overview of the main features:

* a powerful page layout system supporting columns, running headers/footers,
  floatable elements and footnotes
* support for figures and (large) tables
* automatic generation of table of contents and index
* automatic numbering and cross-referencing of section headings, figures and
  tables
* configure one of the included document templates or create your own
* an intuitive style sheet system inspired by CSS
* modular design allowing for multiple frontends (such as reStructuredText,
  Markdown, DocBook, ...)
* handles OpenType, TrueType and Type1 fonts with support for advanced
  typographic features such as kerning, ligatures, small capitals and old style
  figures
* embeds PDF, PNG and JPEG images, preserving transparency and color profiles
* easy to install and deploy; pure-Python with few dependencies
* built on Unicode; ready for non-latin languages

rinohtype's primary input format is reStructuredText_. The ``rinoh`` command
line tool renders reStructuredText documents and the included Sphinx_ builder
makes it possible to output large documents with your own style applied. Have
a look at the `rinohtype documentation`_ for an example of the output.

.. _documentation: http://www.mos6581.org/rinohtype/
.. _create a ticket: https://github.com/brechtm/rinohtype/issues/new/choose
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _Sphinx: http://sphinx-doc.org
.. _rinohtype documentation: http://www.mos6581.org/rinohtype/_downloads/rinohtype.pdf


Requirements
------------

rinohtype supports Python 3.5 and up. For parsing reStructuredText and
CommonMark documents, rinohtype depends on docutils_ and recommonmark_
respectively. pip_ takes care of these requirements when you install rinohtype.

Syntax highlighting of code blocks is eneabled if Pygments_ is installed, which
will be installed automatically with Sphinx_. If you want to include images
other than PDF, PNG or JPEG, you also need to install Pillow_.

.. _docutils: http://docutils.sourceforge.net/index.html
.. _recommonmark: https://recommonmark.readthedocs.io
.. _pip: https://pip.pypa.io
.. _Pygments: https://pygments.org
.. _Pillow: http://python-pillow.github.io


Getting Started
---------------

Installation is trivial::

    pip install rinohtype


reStructuredText Renderer
~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to get started with rinohtype is to render a reStructuredText
document (such as ``CHANGES.rst`` from this repository) using the ``rinoh``
command line tool::

   rinoh CHANGES.rst

When ``rinoh`` finishes, you will find ``CHANGES.pdf`` alongside the input
file.

By default ``rinoh`` renders the input document using the article template. Run
``rinoh --help`` to see how you can tell ``rinoh`` which document template and
style sheet to use.


Sphinx Builder
~~~~~~~~~~~~~~

rinohtype can be used as a drop-in replacement for the LaTeX builder (the
``latex_documents`` configuration variable has to be set). Simply select the
`rinoh` builder when building the Sphinx project::

    sphinx-build -b rinoh . _build/rinoh


Contributing
------------

See ``CONTRIBUTING.rst`` and ``DEVELOPING.rst``


License
-------

All of rinohtype's source code is licensed under the `Affero GPL 3.0`_, unless
indicated otherwise in the source file (such as ``hyphenator.py``).

The Affero GPL requires for software that builds on rinohtype to also be
released as open source under this license. For building closed-source
applications, you can obtain a `commercial license`_. The author of rinohtype
is also available for consultancy projects involving rinohtype.

.. _Affero GPL 3.0: https://www.gnu.org/licenses/agpl-3.0.html
.. _commercial license: brecht.machiels@opqode.com
