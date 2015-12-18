.. _introduction:

Introduction
============

Design Concepts
---------------

RinohType was initially conceived as a modern replacement for LaTeX. An
important goal in the design of RinohType is for documents to be much easier to
customize than in LaTeX. By today's standards, the arcane TeX macro language
upon which LaTeX is built makes customization unnecessarily difficult for one.
Simply being built with Python makes RinohType already much easier to approach
than TeX. Additionally, RinohType is built around the following core concepts to
ensure customizability:


Document templates
    These determine the page layout and (for longer documents) the different
    parts of your document.

Style sheets
    The CSS-inspired style sheets determine the look of individual document
    elements.

Structured Input
    RinohType renders a document from a document tree that does not describe any
    style aspects but only describes semantics. The style sheet maps specific
    style properties to the elements in this document tree. The document tree
    can be generated from a structured document format such as reStructuredText
    and DocBook using one of the included parsers, or it can be built manually.


As RinohType is implemented as a Python package, it doubles as a high-level
PDF library. It's modular design makes it easy to to customize and extend for
specific applications. Because RinohType's source code is open, all of its
internals can be inspected and even modified, making it extremely customizable.

One RinohType's key design concepts is to limit the core's size to keep things
simple but make it easy to build extensions. Currently the core of RinohType
(excluding frontends, backends and font parsers) consists of less than 4000
lines.


Usage Examples
--------------

RinohType supports three modes of operation. These are discussed in more detail
in :ref:`quickstart` guide.


reStructuredText Renderer
~~~~~~~~~~~~~~~~~~~~~~~~~

RinohType comes with a command-line tool ``rinoh`` that can render
reStructuredText documents. Rendering the reStructuredText demonstration article
demo.txt_ (using the standard article template and style sheet) generates
:download:`demo.pdf`.

.. _demo.txt: http://docutils.sourceforge.net/docs/user/rst/demo.txt


Sphinx Builder
~~~~~~~~~~~~~~

.. |common| replace:: Configuring RinohType as a builder for Sphinx allows
                      rendering a Sphinx project to PDF without the need for a
                      LaTeX installation.

.. only:: not rinoh

    |common| This documentation was rendered by RinohType to
    :download:`rinoh.pdf`.

.. only:: rinoh

    |common| This very document you are reading was rendered using
    RinohType's Sphinx builder.


High-level PDF library
~~~~~~~~~~~~~~~~~~~~~~

RinohType can be used in a Python application to generate PDF documents. This
basically involves three choices:

    1. You can use one of the **document templates** included with RinohType and
       optionally customize it to your needs. Or you can create a custom
       template from scratch.
    2. Choose to start from one of included **style sheets** or roll your own.
    3. The **document tree** can be parsed from a structured document format
       such as reStructuredText or built manually using building blocks provided
       by RinohType.

       Both approaches allow for parts of the content to be fetched from a
       database or other data sources. When parsing the document tree from a
       structured document format, a templating engine like Jinja2_ can be used.

.. _Jinja2: http://jinja.pocoo.org

.. todo:: sample documents
