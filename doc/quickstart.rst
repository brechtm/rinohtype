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
:option:`sphinx:sphinx-build -b` option::

    sphinx-build -b rinoh . _build/rinoh

Just like the :program:`rinoh` command line tool, the Sphinx builder requires
two :ref:`rendering passes <rendering_passes>`.


.. _library_quickstart:

High-level PDF Library
~~~~~~~~~~~~~~~~~~~~~~

.. note:: The focus of rinohtype development is currently on the
    :program:`rinoh` tool and Sphinx builder. Use as a Python library is
    possible, but documentation may be lacking. Please be patient.

The most basic way to use rinohtype in an application is to hook up an included
frontend, a document template and a style sheet:

.. testsetup:: my_document

    import os, shutil, tempfile

    lastdir = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    os.chdir(tmpdir)
    shutil.copy(os.path.join(lastdir, 'my_article.rtt'), tmpdir)
    with open('my_document.rst', 'w') as rst_file:
        rst_file.write('Hello World!')

.. testcleanup:: my_document

    os.chdir(lastdir)
    shutil.rmtree(tmpdir)


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
covered the the sections below.

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

.. _quickstart_stylesheets:

Style Sheets
~~~~~~~~~~~~

.. currentmodule:: rinoh.style

A style sheet determines the look of each of the elements in a document. For
each type of document element, the style sheet object registers a list of style
properties. Style sheets are stored in plain text files using the Windows
INI\ [#ini]_ format with the ``.rts`` extension. Below is an excerpt from the
:doc:`sphinx_stylesheet` included with rinohtype.

.. _base style sheet:

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
style sheet based on the Sphinx stylesheet included with rinohtype.

.. code-block:: ini

    [STYLESHEET]
    name=My Style Sheet
    description=Small tweaks made to the Sphinx style sheet
    base=sphinx

    [VARIABLES]
    mono_typeface=Courier

    [emphasis]
    font_color=#00a

    [strong]
    base=DEFAULT_STYLE
    font_color=#a00

By default, styles defined in a style sheet *extend* the corresponding style
from the base style sheet. In this example, emphasized text will be set in an
italic font (as configured in the `base style sheet`_) and colored blue (#00a).

It is also possible to completely override the style definition. This can be
done by setting the ``base`` of a style definition to ``DEFAULT_STYLE`` as
illustrated by the `strong` style. This causes strongly emphasised text to be
displayed in red (#a00) but **not** in a bold font as defined in the `base
style sheet`_ (the default for ``font_weight`` is `Medium`; see
:class:`~rinoh.text.TextStyle`).

The style sheet also redefines the ``mono_typeface`` variable. This variable is
used in the `base style sheet`_ in all style definitions where a monospaced
font is desired. Redefining the variable affects all of these style
definitions.


Starting from Scratch
---------------------

If you don't specify a base style sheet in the ``[STYLESHEET]`` section, you
create an independent style sheet. You should do this if you want to create
a document style that is not based on an existing style sheet. If the style
definition for a particular document element is not included in the style
sheet, the default values for its style properties are used.

Unless a custom :class:`StyledMatcher` is passed to :class:`StyleSheetFile`,
the default matcher is used. Providing your own matcher offers even more
customizability, but it is unlikely you will need this. See the :ref:`matchers`
section in :ref:`advanced` for details.

.. note:: In the future, rinohtype will be able to generate an empty INI style
    sheet, listing all styles defined in the matcher with the supported style
    attributes along with the default values as comments. This generated style
    sheet can serve as a good starting point for developing a custom style
    sheet from scratch.


.. _templates_quickstart:

Document Templates
~~~~~~~~~~~~~~~~~~

.. currentmodule:: rinoh.template

As with style sheets, you can choose to make use of a template provided by
rinohtype and optionally customize it or you can create a custom template from
scratch.


Configuring a Template
----------------------

rinohtype provides a number of :ref:`document_templates`. These can be
customized by means of a template configuration file; a plain text file in the
INI\ [#ini]_ format with the ``.rtt`` extension. The example from
:ref:`library_quickstart` above can be customized using the following template
configuration, for example:

.. literalinclude:: /my_article.rtt
    :language: ini

The ``TEMPLATE_CONFIGURATION`` sections collects global template options. Set
*name* to provide a short label for your template configuration. *template*
identifies the :ref:`document template <document_templates>` to configure.

All document templates consist of a number of document parts. The
:class:`.Article` template defines three parts: :attr:`~.Article.title`,
:attr:`~.Article.front_matter` and :attr:`~.Article.contents`. The order of
these parts can be changed (although that makes little sense for the article
template), and individual parts can optionally be hidden by setting the
:attr:`~.DocumentTemplate.parts` configuration option. The configuration above
hides the front matter part (commented out using a semicolon), for example.

The template configuration also specifies which style sheet is used for styling
document elements. The :class:`.DocumentTemplate.stylesheet` option takes the
name of an installed style sheet (see :option:`rinoh --list-stylesheets`) or
the filename of a stylesheet file (``.rts``).

The :class:`~.DocumentTemplate.language` option sets the default language for
the document. It determines which language is used for standard document
strings such as section and admonition titles.

The :class:`.Article` template defines two custom template options. The
:class:`~.Article.abstract_location` option determines where the (optional)
article abstract is placed, on the title page or in the front matter part.
:class:`~.Article.table_of_contents` allows hiding the table of contents
section. Empty document parts will not be included in the document. When the
table of contents section is suppressed and there is no abstract in the input
document or :class:`~.Article.abstract_location` is set to title, the front
matter document part will not appear in the PDF.

The standard document strings configured by the
:class:`~.DocumentTemplate.language` option described above can be overridden
by user-defined strings in the :class:`SectionTitles` and
:class:`AdmonitionTitles` sections of the configuration file. For example, the
default title for the table of contents section (*Table of Contents*) is
replaced with *Contents*. The configuration also sets custom titles for the
caution and warning admonitions.

The others sections in the configuration file are the ``VARIABLES`` section,
followed by document part and page template sections. Similar to style sheets,
the variables can be referenced in the template configuration sections. Here,
the ``paper_size`` variable is set, which is being referenced by by all page
templates in :class:`Article` (although indirectly through the
:class:`~.Article.page` base page template).

For document part templates, :class:`~.DocumentPartTemplate.page_number_format`
determines how page numbers are formatted. When a document part uses the same
page number format as the preceding part, the numbering is continued.

The :class:`.DocumentPartTemplate.end_at_page` option controls at which page
the document part ends. This is set to ``left`` for the title part in the
example configuration to make the contents part start on a right page.

Each document part finds page templates by name. They will first look for
specific left/right page templates by appending ``_left_page`` or
``_right_page`` to the document part name. If these page templates have not
been defined in the template, it will look for the more general
``<document part name>_page`` template. Note that, if left and right page
templates have been defined by the template (such as the book template), the
configuration will need to override these, as they will have priority over the
general page template defined in the configuration.

The example configuration only adjusts the top margin for the
:class:`TitlePageTemplate`, but many more aspects of the page templates are
configurable. Refer to :ref:`document_templates` for details.

.. todo:: base for part template?

A template configuration file can be specified when rendering using the
command-line :program:`rinoh` tool or :ref:`Sphinx_builder` by passing it to
the :option:`--template <rinoh --template>` command-line option or setting the
:confval:`rinoh_template` option in ``conf.py``, respectively. To render a
document using this template configuration programatically, load the template
file using :class:`.TemplateConfigurationFile`.

.. testcode:: my_document

    from rinoh.frontend.rst import ReStructuredTextReader
    from rinoh.template import TemplateConfigurationFile

    # the parser builds a rinohtype document tree
    parser = ReStructuredTextReader()
    with open('my_document.rst') as file:
        document_tree = parser.parse(file)

    # load the article template configuration file
    config = TemplateConfigurationFile('my_article.rtt')

    # render the document to 'my_document.pdf'
    document = config.document(document_tree)
    document.render('my_document')

.. testoutput:: my_document
    :hide:

    ...
    Writing output: my_document.pdf

The :meth:`.TemplateConfigurationFile.document` method creates a document
instance with the template configuration applied. So if you want to render your
document using a different template configuration, it suffices to load the new
configuration file.

Refer to the :class:`.Article` documentation to discover all of the options
accepted by it and the document part and page templates.


.. todo:: what to include here, what in advanced?


Customizing a Template
----------------------

If you need to customize a template beyond what is possible by configuration,
you can subclass the :class:`Article` (or other) template class and extend it,
or override document part and page templates with custom templates.

.. testcode:: subclass_article

    from rinoh.attribute import OverrideDefault
    from rinoh.template import DocumentPartTemplate, PageTemplate
    from rinoh.templates import Article


    class BibliographyPartTemplate(DocumentPartTemplate):
        ...


    class MyTitlePageTemplate(PageTemplate):
        ...


    class MyArticle(Article):
        parts = OverrideDefault(['title', 'contents', 'bibliography'])

        # default document part templates
        bibliography = BibliographyPartTemplate()

        # default page templates
        title_page = MyTitlePageTemplate(base='page')
        bibliography_page = PageTemplate(base='page')


:class:`MyArticle` extends the :class:`.Article` template, adding the extra
:attr:`~.MyArticle.bibliography` document part, along with the page template
:attr:`~.MyArticle.bibliography_page`. The new document part is included in
:attr:`~.DocumentTemplate.parts`, while also leaving out
:attr:`~.Article.front_matter` by default. Finally, the template also replaces
the title page template with a custom one.


Creating a Custom Template
--------------------------

A new template can be created from scratch by subclassing
:class:`DocumentTemplate`, defining all document parts, their templates and
page templates.

The :class:`.Article` and :class:`.Book` templates are examples of templates
that inherit directly from :class:`DocumentTemplate`. We will briefly discuss
the article template here. The :class:`.Article` template overrides the default
style sheet and defines the two custom template attributes discussed in
`Configuring a Template`_ above. The document parts :attr:`~.Article.title`,
:attr:`~.Article.front_matter` and :attr:`~.Article.contents` are listed the in
:attr:`~.Article.parts` attribute and templates for each of them are provided
along with page templates:

.. literalinclude:: /../src/rinoh/templates/article.py
    :pyobject: Article

The custom :class:`.ArticleFrontMatter` template reads the values for the
two custom template attributes defined in :class:`.Article` to determine which
flowables are included in the front matter:

.. literalinclude:: /../src/rinoh/templates/article.py
    :pyobject: ArticleFrontMatter

Have a look at the :doc:`src/book` for an example of a slightly more complex
template that defines separate templates for left and right pages.


.. footnotes

.. [#ini] see *Supported INI File Structure* in :mod:`python:configparser`
