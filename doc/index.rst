.. rinohtype documentation master file, created by
   sphinx-quickstart on Sat Jan 31 16:06:11 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

rinohtype: The Python Document Processor
========================================

rinohtype is a Python library, including a Sphinx builder, for creating
typeset PDFs from a structured document source. Its focus is on complex
documents such as technical manuals, but it can be used to create any kind of
document.

It processes reStructuredText and Markdown source and builds its output using
Python-based templates and CSS-inspired stylesheets. Through its granular API
and programmatic approach to document structures it makes possible a
repeatable, consistent document generation workflow.

rinohtype addresses a need for accessible and extensible methods of PDF
creation, that include sophisticated control of styling and presentation for
complex materials, alongside well-established workflows for HTML.

rinohtype is especially useful for maintainers of information in rST and
Markdown who want to provide PDF verions of their content.

------

.. todolist::

Release v\ |version|. (:ref:`Release History <changelog>`)

Included with rinohtype is the :program:`rinoh` command line tool that renders
reStructuredText and Markdown (CommonMark) documents. There is also a
commercial DITA_ frontend, but its development is currently on hold. Please
`contact me`_ if you are interested in testing it.

rinohtype also includes support for Sphinx_, which helps writing large
structured documents and supports a multitude of different output formats
including searchable HTML. rinohtype adds support to produce PDF output.

.. _DITA: https://en.wikipedia.org/wiki/Darwin_Information_Typing_Architecture
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
commercial license. I am also available for consultancy projects involving
rinohtype, so don't hesitate to `contact me`_.

.. _GNU AGPL 3.0: http://www.gnu.org/licenses/agpl-3.0.en.html
.. _contact me: brecht@opqode.com


.. include:: manual.rst

.. include:: reference.rst
