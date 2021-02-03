.. rinohtype documentation master file, created by
   sphinx-quickstart on Sat Jan 31 16:06:11 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

rinohtype: The Python Document Processor
========================================

.. todolist::

Release v\ |version|. (:ref:`Release History <changelog>`)

rinohtype is a Python library that transforms a structured document into a
professionally typeset PDF guided by a document template and style sheet. It
can be used to create any kind of document, but its focus is on complex
documents such as technical manuals.

Included with rinohtype is the :program:`rinoh` command line tool that renders
reStructuredText and Markdown (CommonMark) documents. Support for DITA_ is
available in the commercially supported Pro version.

rinohtype also includes support for Sphinx_, which helps writing large
structured documents and supports a multitude of different output formats
including searchable HTML. rinohtype adds support to produce PDF output.

.. _DITA: http://dita.xml.org/standard
.. _Sphinx: http://sphinx-doc.org


Here is a list of rinohtype's main features:

* a powerful page layout system supporting columns, running headers/footers,
  floatable elements and footnotes
* figures, large tables and automatically generated table of contents
* automatic numbering and cross-referencing of sections, figures and tables
* use one of the highly configurable included document templates or create your
  own custom template
* the intuitive style sheets make it easy to change the style of individual
  document elements
* modular design allowing for multiple frontends (such as reStructuredText,
  Markdown, DocBook, ...) and backends (PDF, SVG, bitmap, ...)
* handles OpenType, TrueType and Type1 fonts with support for advanced
  typographic features such as kerning, ligatures and small capitals
* embeds PDF, PNG and JPEG images, preserving transparency and color profiles
* easy to deploy; pure-Python with few dependencies
* built on Unicode; ready for non-latin languages


rinohtype is currently in a beta phase. We are working toward a first stable
release.

rinohtype is open source software licensed under the `GNU AGPL 3.0`_.
Practically, this means you are free to use it in open-source software, but not
in (commercial) closed-source software. For the latter, you need to obtain a
commercial license. We are also available for consultancy projects involving
rinohtype, so don't hesitate to `contact us`_.

.. _GNU AGPL 3.0: http://www.gnu.org/licenses/agpl-3.0.en.html
.. _contact us: info@opqode.com


.. toctree::
    :maxdepth: 2

    intro
    install
    quickstart
    basicstyling
    elementstyling
    templates
    reference
    api/api
    faq
    contributing
    developing
    changelog


.. only:: html

    Indices and tables
    ==================

    * :ref:`genindex`
    * :ref:`modindex`
