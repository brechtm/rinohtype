.. _introduction:

Introduction
============

rinohtype was initially conceived as a modern replacement for LaTeX_. An
important goal in the design of rinohtype is for documents to be much easier to
customize than in LaTeX. By today's standards, the arcane TeX macro language
upon which LaTeX is built makes customization unnecessarily difficult for one.
Simply being built with Python makes rinohtype already much easier to approach
than TeX. Additionally, rinohtype is built around the following core concepts
to ensure customizability:

Document Templates
    These determine the page layout and (for longer documents) the different
    parts of your document. The templates included with rinohtype are highly
    configurable and allow changing margins, headers, footers, chapter titles,
    etc. If this is not sufficient, a custom template can be created.

Style Sheets
    The CSS-inspired style sheets determine the look of individual document
    elements. A style sheet assigns style attributes to each type of document
    element. For example, a paragraph's style is determined by the typeface,
    font weight, size and color, horizontal alignment of text etc.

Structured Input
    rinohtype renders a document from a document tree that does not describe
    any style aspects but only semantics. The style sheet maps specific style
    properties to the elements in this document tree. The document tree can be
    automatically generated from a structured document format such as
    reStructuredText and CommonMark using one of the included frontends, or it
    can be constructed manually.

rinohtype is implemented as a Python package and doubles as a high-level PDF
library. Its modular design makes it easy to to customize and extend for
specific applications. Moreover, because rinotype's source code is open, all of
its internals can be inspected and even modified, making it customizable at all
levels.

.. _LaTeX: http://en.wikipedia.org/wiki/LaTeX


Usage Examples
--------------

rinohtype supports three modes of operation, which are discussed in more detail
in the :ref:`quickstart` guide. For each of these modes, you can choose to use
one of the document templates included with rinohtype or a third-party template
available from PyPI and optionally customize it to your needs. Or you can
create a custom template from scratch. The same is true for the style sheet
used to style the document elements.


Command-Line Renderer
~~~~~~~~~~~~~~~~~~~~~

rinohtype includes the :program:`rinoh` command-line tool which renders
structured text documents. Currently, reStructuredText_ and CommonMark_
documents are supported in the open-source version. Support for DITA_ is
available in the commercially supported Pro version.

Rendering the reStructuredText demonstration article `demo.txt`_ (using the
standard article template and style sheet) generates :download:`demo.pdf
<../tests_regression/reference/demo.pdf>`.

.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _CommonMark: http://commonmark.org
.. _DITA: http://dita.xml.org/standard
.. _demo.txt: http://docutils.sourceforge.net/docs/user/rst/demo.txt


Sphinx Builder
~~~~~~~~~~~~~~

.. |common| replace:: Configuring rinohtype as a builder for Sphinx allows
                      rendering a Sphinx project to PDF without the need for a
                      LaTeX installation.

.. only:: not rinoh

    |common| This documentation was rendered by rinohtype to
    :download:`rinohtype.pdf <_build/rinoh/rinohtype.pdf>`.

.. only:: rinoh

    |common| This very document you are reading was rendered using
    rinohtype's Sphinx builder.


High-level PDF library
~~~~~~~~~~~~~~~~~~~~~~

rinohtype can also be used as a Python library to generate PDF documents. Just
like with :program:`rinoh` and the Sphinx builder, you can select which
document template and style sheet to use.

Additionally, you need to supply a document tree. This document tree can be
parsed from a structured document format such as reStructuredText by using one
of the provided frontends or built manually using building blocks provided by
rinohtype. You can also write a frontend for a custom format such as an XML
dialect.

All of these approaches allow for parts of the content to be fetched from a
database or other data sources. When parsing the document tree from a
structured document format, a templating engine like Jinja2_ can be used.

.. _Jinja2: http://jinja.pocoo.org

.. todo:: sample documents
