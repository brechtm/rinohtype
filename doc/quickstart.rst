.. _quickstart:

Quickstart
==========

This section gets you started quickly, discussing each of the three modes of
operation introduced in :ref:`Introduction`. Additionally, the basics of style
sheets and document templates are explained.


reStructuredText Renderer
~~~~~~~~~~~~~~~~~~~~~~~~~

Installing rinohtype places the :program:`rinoh` script in the :envvar:`PATH`.
This can be used to render reStructuredText_ documents such as `demo.txt`_::

    rinoh demo.txt

After rendering finishes, you will find ``demo.pdf`` alongside the input file.

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

To use rinohtype to render Sphinx documents, at a minimum you need to add
``'rinoh.frontend.sphinx'`` to the ``extensions`` list in the Sphinx
project's ``conf.py``.

If your Sphinx project is already configured for rendering with LaTeX,
rinohtype will happily interpret :confval:`sphinx:latex_documents` and other
options for the LaTeX builder. Otherwise, you need to set the
:confval:`rinoh_documents` configuration option::

    rinoh_documents = [('index',            # top-level file (index.rst)
                        'target',           # output (target.pdf)
                        'Document Title',   # document title
                        'John A. Uthor')]   # document author

Other configuration variables are optional and allow configuring the style of
the generated PDF document. See :ref:`sphinx_builder` for details.

When building the documentation, select the `rinoh` builder by passing it to
:program:`sphinx-build`'s :option:`sphinx:-b` option::

    sphinx-build -b rinoh . _build/rinoh

Just like the :program:`rinoh` command line tool, the Sphinx builder requires
two :ref:`rendering passes <rendering_passes>`.


.. _library_quickstart:

High-level PDF Library
~~~~~~~~~~~~~~~~~~~~~~

.. note:: The focus of rinohtype development is currently on the
    :program:`rinoh` tool and Sphinx builder at this moment. Use as a Python
    library is possible, but documentation may be lacking. Please be patient.

The most basic way to use rinohtype in an application is to hook up an included
frontend, a document template and a style sheet:

.. testsetup:: my_document

    import os, shutil, tempfile

    lastdir = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    os.chdir(tmpdir)
    with open('my_document.rst', 'w') as rst_file:
        rst_file.write('Hello World!')


.. testcleanup:: my_document

    os.chdir(lastdir)
    shutil.rmtree(tmpdir)

.. testcode:: my_document

    from rinoh.backend import pdf
    from rinoh.frontend.rst import ReStructuredTextReader
    from rinoh.templates import Article

    # the parser builds a rinohtype document tree
    parser = ReStructuredTextReader()
    with open('my_document.rst') as file:
        document_tree = parser.parse(file)

    # render the document to 'my_document.pdf'
    document = Article(document_tree, backend=pdf)
    document.render('my_document')

.. testoutput:: my_document
    :hide:

    ...
    Writing output: my_document.pdf


This basic application can be customized to your specific requirements by
customizing the document template, the style sheet and the way the document's
content tree is built. The basics of document templates and style sheets are
covered the the sections below.

The document tree returned by the :class:`ReStructuredTextReader` in the
example above can also be built manually. A :class:`DocumentTree` is simply a
list of :class:`Flowable`\ s, which can have child elements. These children in
turn can also have children, and so on; together they form a tree.

Here is an example document tree of a short article:

.. testcode:: document_tree

    from rinoh.document import DocumentTree
    from rinoh.styleds import *

    document_tree = DocumentTree('/path/to/source_file.ext',
                    [Paragraph('My Document', style='title'), # metadata!
                     Section([Heading('First Section'),
                              Paragraph('This is a paragraph with some'
                                        + Emphasized('emphasized text')
                                        + 'and an'
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

.. todo:: make ``source_path`` optional

It is clear that this type of content is best parsed from a structured document
format such as reStructuredText or XML. Manually building a document tree is
well suited for short, custom documents however.

.. _quickstart_stylesheets:

Style Sheets
~~~~~~~~~~~~

A style sheet determines the look of each of the elements in a document. For
each type of document element, the style sheet object registers a list of style
properties. Style sheets are stored in plain text files using the INI format
with the ``.rts`` extension. Below is an excerpt from the `Sphinx` style sheet
included with rinohtype.

.. literalinclude:: /../src/rinoh/data/stylesheets/sphinx.rts
    :language: ini
    :end-before: [italic]

Except for ``[STYLESHEET]`` and ``[VARIABLES]``, each configuration section
in a style sheet determines the style of a particular type of document element.
The ``emphasis`` style, for example, determines the look of emphasized text,
which is displayed in an italic font. For more on style sheets, please refer
to the :ref:`stylesheets_advanced` section in :ref:`advanced`.

This is similar to how HTML's cascading style sheets work. In rinohtype
however, document elements are identified by means of a descriptive label (such
as *emphasis*) instead of a cryptic selector. Rinohtype also makes use of
selectors, but these are collected in a :class:`StyledMatcher` which maps them
to descriptive names to be used by many style sheets. Unless you are using
rinohtype as a PDF library to create custom documents, the default matcher
should cover your needs.


Extending an Existing Style Sheet
---------------------------------

Starting from an existing style sheet, it is easy to make small changes to the
style of individual document elements. The following example creates a new
style sheet based on the Sphinx stylesheet included with rinohtype. The style
sheet redefines the style for emphasized text, displaying it in a bold instead
of italic font.

.. code-block:: ini

    [STYLESHEET]
    name=My Style Sheet
    description=Small tweaks made to the Sphinx style sheet
    base=sphinx

    [VARIABLES]
    mono_typeface=Courier

    [emphasis]
    font_slant=bold

This style sheet also redefines the ``mono_typeface`` variable. This variable
is used in the Sphinx style sheet in all style definitions where a monospaced
font is desired. Redefining the variable affects all of these style
definitions.

    .. todo:: How to do this in a INI style sheet?

        Here, the new new style definition completely replaces the style
        definition contained in the Sphinx style sheet. It is also possible to
        override only part of the style definition. The following style
        definition changes only the item spacing between enumerated list items.
        All other style properties (such as the left margin and the item
        numbering format) remain unchanged.


        .. code-block:: python

            my_style_sheet('enumerated list', base=styles['default'],
                           flowable_spacing=3*PT)

To use this style sheet, load it using :class:`StyleSheetFile`:

.. code-block:: python

    from rinoh.style import StyleSheetFile

    my_stylesheet = StyleSheetFile('m_stylesheet.rts')



Starting from Scratch
---------------------

If you don't specify a base style sheet in the ``[STYLESHEET]`` section, you
create an independent style sheet. You should do this if you want to create
a document style that is radically different from what is provided by existing
style sheets.

If the style definition for a particular document element is missing, the
default values for its style properties are used.

To use this style sheet, you need to specify the :class:`StyledMatcher` to use,
since there is not base providing one. The following example uses the standard
matcher:

.. code-block:: python

    from rinoh.style import StyleSheetFile
    from rinoh.stylesheets import matcher

    my_stylesheet = StyleSheetFile('m_stylesheet.rts', matcher=matcher)


.. note:: In the future, rinohtype will allow generating an INI style sheet,
    listing all matched elements and their style attributes together with the
    default values.



Document Templates
~~~~~~~~~~~~~~~~~~

As with style sheets, you can choose to make use of the templates provided by
rinohtype and optionally customize it or you can create a custom template from
scratch.


Using an Existing Template
--------------------------

Rinohtype provides a number of :ref:`document_templates`. These can be
customized by passing an instance of the associated
:class:`rinoh.template.TemplateConfiguration` as `configuration` on template
instantiation.

The example from :ref:`library_quickstart` above can be customized by setting
template options.

.. testcode:: my_document

    from rinoh.backend import pdf
    from rinoh.dimension import CM
    from rinoh.frontend.rst import ReStructuredTextReader
    from rinoh.paper import A5
    from rinoh.stylesheets import sphinx_base14
    from rinoh.templates import Article

    # the parser builds a rinohtype document tree
    parser = ReStructuredTextReader()
    with open('my_document.rst') as file:
        document_tree = parser.parse(file)

    # customize the article template
    configuration = Article.Configuration(paper_size=A5,
                                          stylesheet=sphinx_base14,
                                          abstract_location='title',
                                          table_of_contents=False)
    configuration('title_page', top_margin=2*CM)

    # render the document to 'my_document.pdf'
    document = Article(document_tree, configuration=configuration, backend=pdf)
    document.render('my_document')

.. testoutput:: my_document
    :hide:

    ...
    Writing output: my_document.pdf

Here, a number of global template settings are specified to override the
default values. For example, the paper size is changed to A5 from the default
A4. See below for a list of the settings that can be changed and their
description.

The top margin of the title page is also changed by setting the corresponding
option for the :attr:`rinoh.templates.article.ArticleConfiguration.title_page`
page template.


Creating a Custom Template
--------------------------

A custom template can be created by inheriting from :class:`DocumentTemplate`.
The :attr:`parts` attribute determines the global structure of the document. It
is a list of :class:`DocumentPartTemplate`\ s, each referencing a page
template.

The :class:`rinoh.templates.article.Article` template, for example, consists of
a title page, a front matter part (a custom
:class:`rinoh.template.DocumentPartTemplate` subclass) and the article
contents:

.. literalinclude:: /../src/rinoh/templates/article.py
    :pyobject: Article


The :class:`TemplateConfiguration` subclass associated with :class:`Article`

- overrides the default style sheet,
- introduces configuration attributes to control the table of contents
  placement and the location of the abstract, and
- defines the page templates referenced in :attr:`Article.parts`

.. literalinclude:: /../src/rinoh/templates/article.py
    :pyobject: ArticleConfiguration

The configuration attributes are used in the custom front matter document part
template:

.. literalinclude:: /../src/rinoh/templates/article.py
    :pyobject: ArticleFrontMatter
