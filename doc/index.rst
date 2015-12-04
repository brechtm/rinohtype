.. RinohType documentation master file, created by
   sphinx-quickstart on Sat Jan 31 16:06:11 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

RinohType: The Python Document Processor
========================================

Release v\ |version|. (:ref:`Release History <changelog>`)

RinohType is the heavy-duty PDF library for Python. It helps automating the
creation of any type of document, ranging from invoices to long, complex
technical documents.

Additionally, RinohType offers a modern alternative to LaTeX_ when paired with
Sphinx_. Sphinx helps writing large documents and supports a multitude of
different output formats including searchable HTML. RinohType includes a Sphinx
backend that allows generating beautiful PDF documents.

.. _Sphinx: http://sphinx-doc.org
.. _LaTeX: http://en.wikipedia.org/wiki/LaTeX


Here is a list of RinohType's most important features:

* built on Unicode; ready for non-latin languages
* a powerful page layout system supporting columns, running headers/footers,
  floatable elements and footnotes
* figures, large tables and automatically generated table of contents
* cross-references and automatic numbering of headings, figures and tables
* use one of the included document templates or create your own
* an intuitive style sheet system inspired by CSS
* modular design allowing for multiple frontends (such as reStructuredText,
  Markdown, DocBook, ...) and backends (PDF, SVG, bitmap, ...)
* handles OpenType, TrueType and Type1 fonts with support for advanced
  typographic features such as kerning, ligatures and small capitals
* embeds PDF, PNG and JPEG images, preserving transparency and color profiles
* easy to deploy; pure-Python with few dependencies


RinohType is currently in a beta phase. We are working toward a first stable
release.

RinohType is open source software licensed under the `GNU AGPL 3.0`_.
Practically, this means you are free to use it in open-source software, but not
in (commercial) closed-source software. For this purpose, you need a commercial
license (see http://www.opqode.com/). We are also available for consultancy
projects involving RinohType, so please don't hesitate to contact us.

.. _GNU AGPL 3.0: http://www.gnu.org/licenses/agpl-3.0.en.html


Contents:

.. toctree::
    :maxdepth: 2

    intro
    install
    quickstart
    advanced
    changelog



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

