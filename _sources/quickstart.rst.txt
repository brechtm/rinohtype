.. _quickstart:

Quickstart
==========

This section gets you started quickly, discussing each of the three modes of
operation introduced in :ref:`Introduction`. If you want to customize the style
of the PDF document, please refer to :ref:`basic_styling` which introduces
style sheets and document templates.


Command-Line Renderer
~~~~~~~~~~~~~~~~~~~~~

Installing rinohtype places the :program:`rinoh` script in the :envvar:`PATH`.
This can be used to render structured documents such as `demo.txt`_
(reStructuredText_)::

    rinoh --format reStructuredText demo.txt

After rendering finishes, you will find
:download:`demo.pdf <../tests_regression/reference/demo.pdf>` alongside the
input file.

:program:`rinoh` allows specifying the document template and style sheet to use
when rendering the reStructuredText document. See its :ref:`command-line
options <rinoh>` for details.

.. _rendering_passes:

Two rendering passes are required to make sure that cross-references to page
numbers are correct. After a document has been rendered, rinohtype will save
the page reference data to a `.rtc` file. Provided the document (or the
template or style sheet) doesn't change a lot, this can prevent the need to
perform a second rendering pass.

.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _demo.txt: http://docutils.sourceforge.net/docs/user/rst/demo.txt


.. _sphinx_quickstart:

Sphinx Builder
~~~~~~~~~~~~~~

If your Sphinx project is already configured for the LaTeX builder, rinohtype
will happily interpret :confval:`sphinx:latex_documents`. Otherwise, you need
to set the :confval:`rinoh_documents` configuration option::

    rinoh_documents = [('index',            # top-level file (index.rst)
                        'target',           # output (target.pdf)
                        'Document Title',   # document title
                        'John A. Uthor')]   # document author

Other configuration variables are optional and allow configuring the style of
the generated PDF document. See :ref:`sphinx_builder` for details.

When building the documentation, select the `rinoh` builder by passing it to
the :option:`sphinx:sphinx-build -b` option::

    sphinx-build -b rinoh . _build/rinoh

Note that, just like the :program:`rinoh` command line tool, the Sphinx builder
requires two :ref:`rendering passes <rendering_passes>`.


.. _library_quickstart:

High-level PDF Library
~~~~~~~~~~~~~~~~~~~~~~

.. note:: The focus of rinohtype development is currently on the
    :program:`rinoh` tool and Sphinx builder. Use as a Python library is
    possible, but documentation may be lacking. Please be patient.

The most basic way to use rinohtype in an application is to hook up an included
frontend, a document template and a style sheet:

.. include:: testcode.rst

.. testcode:: my_document

    from rinoh.frontend.rst import ReStructuredTextReader
    from rinoh.templates import Article

    # the parser builds a rinohtype document tree
    parser = ReStructuredTextReader()
    with open('my_document.rst') as file:
        document_tree = parser.parse(file)

    # render the document to 'my_document.pdf'
    document = Article(document_tree)
    document.render('my_document')

.. testoutput:: my_document
    :hide:

    ...
    Writing output: my_document.pdf


This basic application can be customized to your specific requirements by
customizing the document template, the style sheet and the way the document's
content tree is built. The basics of document templates and style sheets are
covered in later sections.

The document tree returned by the :class:`ReStructuredTextReader` in the
example above can also be built manually. A :class:`DocumentTree` is simply a
list of :class:`Flowable`\ s, which can have child elements. These children in
turn can also have children, and so on; together they form a tree.

Here is an example document tree of a short article:

.. testcode:: document_tree

    from rinoh.document import DocumentTree
    from rinoh.styleds import *

    document_tree = DocumentTree(
                        [Paragraph('My Document', style='title'), # metadata!
                         Section([Heading('First Section'),
                                  Paragraph('This is a paragraph with some '
                                            + StyledText('emphasized text',
                                                         style='emphasis')
                                            + ' and an '
                                            + InlineImage('image.pdf')),
                                  Section([Heading('A subsection'),
                                           Paragraph('Another paragraph')
                                          ])
                                 ]),
                         Section([Heading('Second Section'),
                                  List([Paragraph('a list item'),
                                        Paragraph('another list item')
                                       ])
                                 ])
                        ])

It is clear that this type of content is best parsed from a structured document
format such as reStructuredText or XML. Manually building a document tree is
well suited for short, custom documents however.
