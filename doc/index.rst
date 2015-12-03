.. RinohType documentation master file, created by
   sphinx-quickstart on Sat Jan 31 16:06:11 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

RinohType: The Python Document Processor
========================================

Release v\ |version|. (:ref:`Release History <changelog>`)

RinohType can be most easily described as a high-level PDF library for Python.
The term *high-level* refers to the fact that RinohType also handles page and
document layout for you.

Additionally, RinohType offers a modern alternative to LaTeX_ when paired with
Sphinx_. Sphinx helps writing documents and supports a multitude of different
output formats including searchable HTML. RinohType includes a Sphinx backend
that allows generating beautiful PDF documents.

.. _Sphinx: http://sphinx-doc.org
.. _LaTeX: http://en.wikipedia.org/wiki/LaTeX


Here is a list of RinohType's most important features:

* built on Unicode; ready for non-latin languages
* a powerful page layout system supporting columns, running headers/footers,
  floatable elements and footnotes
* figures, large tables and automatically generated table of contents
* autmatic numbering of headings, figures and tables and cross-references
* use one of the included document templates or create your own
* an intuitive style sheet system inspired by CSS
* modular design allowing for multiple frontends (such as reStructuredText,
  Markdown, DocBook, ...) and backends (PDF, SVG, bitmap, ...)
* handles OpenType, TrueType and Type1 fonts with support for advanced
  typographic features such as kerning and ligatures
* embeds PDF, PNG and JPEG images, preserving transparency and color profiles
* easy to deploy; pure-Python with few dependencies


RinohType is currently in a beta phase. We are working toward a first stable
release.

RinohType is free for non-commercial use. For commercial use you need a
commercial license. You can evaluate RinohType free of charge, however. As soon
as you are running RinohType in production, you need a commercial license.



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

