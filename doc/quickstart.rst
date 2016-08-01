.. _quickstart:

Quickstart
==========

This section gets you started quickly, discussing each of the three modes of
operation introduced in :ref:`Introduction`. Additionally, the basics of style
sheets and document templates are explained.


reStructuredText Renderer
~~~~~~~~~~~~~~~~~~~~~~~~~

Installing rinohtype places the ``rinoh`` script in the ``PATH``. This can be
used to render reStructuredText_ documents such as `demo.txt`_::

    rinoh demo.txt

After rendering finishes, you will find ``demo.pdf`` alongside the input file.

``rinoh`` allows specifying the document template and style sheet to use when
rendering the reStructuredText document. See the program options below for
details.

.. autoprogram:: rinoh.tool:parser
   :prog: rinoh

.. todo:: separate page for ``rinoh``

.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _demo.txt: http://docutils.sourceforge.net/docs/user/rst/demo.txt


.. _sphinx_quickstart:

Sphinx Builder
~~~~~~~~~~~~~~

To use rinohtype to render Sphinx documents, at a minimum you need to add
``'rinoh.frontend.sphinx'`` to the ``extensions`` list in the Sphinx
project's ``conf.py``.

If your Sphinx project is already configured for rendering with LaTeX,
rinohtype will happily interpret the :confval:`sphinx:latex_documents` and
other options for the LaTeX builder. Otherwise, you need to set the
:confval:`rinoh_documents` configuration option::

    rinoh_documents = [('index',            # top-level file (index.rst)
                        'target',           # output (target.pdf)
                        'Document Title',   # document title
                        'John A. Uthor')]   # document author

Other configuration variables are optional and allow configuring the style of
the generated PDF document.

When building the documentation, select the `rinoh` builder::

    sphinx-build -b rinoh . _build/rinoh


Options for the Sphinx Builder
------------------------------

.. confval:: rinoh_documents

    Determines how to group the document tree into PDF output files. Its format
    is identical to that of :confval:`sphinx:latex_documents`, with the
    exception that `targetname` should specify the name of the PDF file without
    the extension. If it is not specified, the value of
    :confval:`sphinx:latex_documents` is used instead (with the ``.tex``
    extension stripped from the `targetname`).

.. confval:: rinoh_document_template

    The document template to use for rendering the Sphinx documentation. It can
    be a :class:`DocumentTemplate` subclass or a string identifying an
    installed template. For the latter, see the :option:`--list-templates`
    option of :program:`rinoh`. Default: ``'book'``.

.. confval:: rinoh_template_configuration

    This variable allows configuring the document template specified in
    :confval:`rinoh_document_template`. Its value needs to be an instance of
    the :class:`TemplateConfiguration` subclass associated with the specified
    document template class. Default: ``None``.

.. confval:: rinoh_paper_size

    If no paper size is configured in :confval:`rinoh_template_configuration`,
    this determines the paper size used. This should be a :class:`Paper`
    instance. A set of predefined paper sizes can be found in the
    :mod:`rinoh.paper` module. If not specified, the value of the
    ``'papersize'`` entry in :confval:`sphinx:latex_elements` is converted to
    the equivalent :class:`Paper`. If this is not specified, the value
    specified for :confval:`sphinx:latex_paper_size` is used.

.. confval:: rinoh_stylesheet

    If :confval:`rinoh_template_configuration` does not specify a style sheet,
    this variable specifies the style sheet used to style the document
    elements. It can be a :class:`StyleSheet` instance or a string identifying
    an installed style sheet. Default: the default style sheet for the chosen
    document template.

    If :confval:`sphinx:pygments_style` is specified, it overrides the code
    highlighting style for the specified or default style sheet.

.. note:: Since the interactions between
    :confval:`rinoh_template_configuration`, :confval:`rinoh_paper_size`,
    :confval:`rinoh_stylesheet` and :confval:`sphinx:pygments_style` are fairly
    complex, this behavior may be changed (simplified) in the future.

.. confval:: rinoh_logo

    Path (relative to the configuration directory) to an image file to use at
    the top of the title page. If not specified, the
    :confval:`sphinx:latex_logo` value is used.

.. confval:: rinoh_domain_indices

    Controls the generation of domain-specific indices. Identical to
    :confval:`sphinx:latex_domain_indices`, which is also used when
    :confval:`rinoh_domain_indices` is not specified.


.. _library_quickstart:

High-level PDF Library
~~~~~~~~~~~~~~~~~~~~~~

.. note:: The focus of rinohtype development is currently on the ``rinoh`` tool
    and Sphinx builder at this moment. Use as a Python library is possible, but
    documentation may be lacking. Please be patient.

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
file such as reStructuredText or XML. Manually building a document tree is well
suited for short, custom documents however.


Style Sheets
~~~~~~~~~~~~

A style sheet determines the look of each of the elements in a document. For
each type of document element, the style sheet object registers a list of style
properties. Style sheets are stored in plain text files using the INI format
with the ``.rts`` extension. Below is an excerpt from the `Sphinx` style sheet
included with rinohtype.

.. literalinclude:: /../rinoh/data/stylesheets/sphinx.rts
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


Building on an Existing Style Sheet
-----------------------------------

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

This style sheet also redefines the variable ``mono_typeface``. This variable
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
since there is not base providing one. The following example used the standard
matcher:

.. code-block:: python

    from rinoh.style import StyleSheetFile
    from rinoh.stylesheets import matcher

    my_stylesheet = StyleSheetFile('m_stylesheet.rts', matcher=matcher)


.. note:: In the future, rinohtype will allow generating an INI style sheet,
    listing all matched elements and their style attributes together with the
    default values.



Documument Templates
~~~~~~~~~~~~~~~~~~~~

As with style sheets, you can choose to make use of the templates provided by
rinohtype and optionally customize it or you can create a custom template from
scratch.


Using an Existing Template
--------------------------

Rinohtype includes two document templates; :class:`Article` and :class:`Book`.
These templates can be customized by passing an instance of respectively
:class:`Article.Configuration` or :class:`Book.Configuration` as
`configuration` on template instantiation.

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

The top margin of the title page is also changed. ``'title_page'`` corresponds
to the :attr:`rinoh.templates.article.ArticleConfiguration.title_page` page
template.

.. todo:: separate pages for the Article and Book templates

The configuration classes specific to :class:`Article` and :class:`Book`
templates are:

.. autoclass:: rinoh.templates.article.ArticleConfiguration
    :show-inheritance:
    :members:

.. autoclass:: rinoh.templates.book.BookConfiguration
    :show-inheritance:
    :members:

Both derive from :class:`TemplateConfiguration` and thus additionally accept
the options offered by it:

.. autoclass:: rinoh.template.TemplateConfiguration
    :members:

The document templates make use of page templates:

.. autoclass:: rinoh.template.PageTemplate
    :show-inheritance:
    :members:

.. autoclass:: rinoh.template.TitlePageTemplate
    :show-inheritance:
    :members:

The base class for these collects the common options:

.. autoclass:: rinoh.template.PageTemplateBase
    :show-inheritance:
    :members:


Creating a Custom Template
--------------------------

A custom template can be created by inheriting from :class:`DocumentTemplate`.
The :attr:`parts` attribute determines the global structure of the document. It
is a list of :class:`DocumentPartTemplate`\ s, each referencing a page
template.

The :class:`Article` template, for example, consists of a title page, a front
matter part (a custom :class:`DocumentPartTemplate` subclass) and the article
contents:

.. literalinclude:: /../rinoh/templates/article.py
    :pyobject: Article


The :class:`TemplateConfiguration` subclass associated with :class:`Article`

- overrides the default style sheet,
- introduces configuration attributes to control the table of contents
  placement and the location of the abstract, and
- defines the page templates referenced in :attr:`Article.parts`

.. literalinclude:: /../rinoh/templates/article.py
    :pyobject: ArticleConfiguration

The configuration attributes are used in the custom front matter document part
template:

.. literalinclude:: /../rinoh/templates/article.py
    :pyobject: ArticleFrontMatter
