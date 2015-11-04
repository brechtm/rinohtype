.. _introduction:

Introduction
============

Design Concepts
---------------

RinohType was initially conceived as a modern replacement for LaTeX. An
important goal in the design of RinohType is for documents to be much easier to
customize than in LaTeX. By today's standards, the arcane TeX macro language
upon which LaTeX is built makes customization unnecessarily difficult for one.
Simply being built with Python makes RinohType much easier to approach than TeX.
Additionally, RinohType is built around the following core concepts to ensure
customizability:


Document templates
    These determine the page layout and (for longer documents) the different
    parts of your document.

Style sheets
    The CSS-inspired style sheets determine the look of individual document
    elements.

Structured Input
    RinohType renders a document from a document tree that does not describe any
    style aspects but only describes semantics. The style sheets map specific
    style properties to elements in this document tree. The document tree can
    be generated from a structured document format such as reStructuredText and
    DocBook using one of the included parsers, or it can be built manually.


As RinohType is implemented as a Python package, it doubles as a high-level
PDF library. It's modular design makes it easy to to customize and extend for
specific applications. Because RinohType's source code is open, all of its
internals can be inspected and event modified, making it extremely customizable.
One RinohType's core concepts is to limit the core's size to keep things simple
but make it easy to build extensions. Currently the core of RinohType (excluding
frontends, backends and font parsers) consists of less than 4000 lines, making
it very accessible to interpretation and modification.


Usage Examples
--------------

RinohType supports three modes of operation. These are discussed in more detail
in :ref:`quickstart`.


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
                      rendering a Sphinx project to PDF.

.. only:: not rinoh

    |common| This documentation was rendered by RinohType to
    :download:`rinoh.pdf`.

.. only:: rinoh

    |common| The this very document you are reading was rendered using
    RinohType's Sphinx builder.


High-level PDF library
~~~~~~~~~~~~~~~~~~~~~~

RinohType can be used in a Python application to generate PDF documents. This
basically involves three choices:

    1. You can use one of the **document templates** included with RinohType and
       optionally customize it to your needs. Or you can create a custom
       template from scratch.
    2. Again, you can choose to start from one of included **style sheets** or
       roll your own.
    3. The document's contents can be provided in a structured document format
       such as reStructuredText. The document tree can also be built
       programmatically using building blocks provided by RinohType, optionally
       with parts fetched from a database or CMS. The document contents can also
       be a combination of these two.

.. todo:: sample documents
