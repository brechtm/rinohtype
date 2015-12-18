.. _quickstart:

Quickstart
==========

This section gets you started quickly, discussing each of the three modes of
operation introduced in :ref:`Introduction`. Additionally, the basics of style
sheets and document templates are explained.


reStructuredText Renderer
~~~~~~~~~~~~~~~~~~~~~~~~~

Installing RinohType places the ``rinoh`` script in the ``PATH``. This can be
used to render reStructuredText_ documents such as `demo.txt`_::

    rinoh demo.txt

After rendering finishes, you will find ``demo.pdf`` alongside the input file.

At this moment, ``rinoh`` does not yet accept many command-line options. It
always renders the reStructuredText document using the article template. You can
however specify the paper size using the ``--paper`` command line argument.

.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _demo.txt: http://docutils.sourceforge.net/docs/user/rst/demo.txt


.. _sphinx_quickstart:

Sphinx Builder
~~~~~~~~~~~~~~

To use RinohType to render Sphinx documents, you need to adjust the Sphinx
project's ``conf.py``:

1. add ``rinoh.frontend.sphinx`` to the ``extensions`` list, and
2. set the ``rinoh_documents`` configuration option::

    rinoh_documents = [('index',            # top-level file (index.rst)
                        'target',           # output (target.pdf)
                        'Document Title',   # document title
                        'John A. Uthor')]   # document author

3. (optional) you can customize some aspects of the document template such as
   margins and headers and footer text by specifying ``rinoh_options``::

    from rinoh.dimension import CM
    from rinoh.reference import Variable, PAGE_NUMBER, NUMBER_OF_PAGES
    from rinoh.text import Tab
    from rinoh.float import InlineImage

    footer_text = (InlineImage('images/company_logo.pdf')
                   + Tab() + Tab()
                   + Variable(PAGE_NUMBER) + ' / ' + Variable(NUMBER_OF_PAGES))

    rinoh_options = dict(header_text=Tab() + project,
                         footer_text=footer_text,
                         page_horizontal_margin=3*CM,
                         page_vertical_margin=4.5*CM)

   The Sphinx builder uses the :class:`Book` document template\ [1]_.
   ``rinoh_options`` are passed to :class:`BookOptions`, so see its
   documentation for details.

4. now we can select the `rinoh` builder when building the documentation::

    sphinx-build -b rinoh . _build/rinoh


High-level PDF library
~~~~~~~~~~~~~~~~~~~~~~

The most basic way to use the RinohType package is to hook up an included
parser, a style sheet and a document template::

    from rinoh.paper import A4
    from rinoh.backend import pdf
    from rinoh.frontend.rst import ReStructuredTextParser

    from rinohlib.stylesheets.sphinx import styles as STYLESHEET
    from rinohlib.templates.article import Article, ArticleOptions


    # the parser builds a RinohType document tree
    parser = ReStructuredTextParser()
    with open('my_document.rst') as rst_file:
        document_tree = parser.parse(rst_file)

    # customize the article template
    article_options = ArticleOptions(page_size=A4, columns=2,
                                     table_of_contents=True,
                                     stylesheet=STYLESHEET)

    # render the document to 'my_document.pdf'
    document = Article(document_tree, options=article_options,
                       backend=pdf)
    document.render('my_document')


This basic application can be customized to your specific requirements by
customizing the style sheet, the document template and the way the document's
content tree is built. The basics of style sheets and document templates are
covered the the sections below.

The document tree returned by the :class:`ReStructuredTextParser` in the
example above can be easily built manually. `document_tree` is simply a list
of :class:`Flowable`\ s. These flowables can have children flowables. These in
turn can also have children, and so on; together they form a tree.

Here is an example document tree of a short article::

    document_tree = [Paragraph('My Document', style='title'), # metadata!
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
                              List([ListItem(Paragraph('a list item')),
                                    ListItem(Paragraph('another list item'))
                                   ])
                             ])
                    ]

It is obvious this type of content is best parsed from a structured document
file such as reStructuredText or XML. Manually building a document tree is well
suited for short, custom documents however. Please refer to the invoice example
for details.


Style Sheets
~~~~~~~~~~~~

A RinohType style sheet is defined in a Pyton source file, as an instance of the
:class:`StyleSheet` class. For each document element, the style sheet object
registers a list of style properties.

This is similar to how HTML's cascading style sheets work. In RinohType however,
style properties are assigned to document elements by means of a descriptive
label for the latter instead of a selector. RinohType also makes use of
selectors, but these are collected in a :class:`StyledMatcher`. Unless you are
using RinohType as a PDF library to creating custom documents, the default
matcher should cover your needs.


Building on an existing style sheet
...................................

Starting from an existing style sheet, it is easy to make small changes to the
style of individual document elements. The following example creates a new
style sheet based on the Sphinx stylesheet included with RinohType. The style
sheet redefines the style for emphasized text, displaying it in a bold instead
of italic font.

.. code-block:: python

    from rinoh.dimension import PT
    from rinoh.font.style import BOLD
    from rinohlib.stylesheets.sphinx import styles

    my_style_sheet = StyleSheet('My Style Sheet', base=styles)

    my_style_sheet('emphasis', font_weight=BOLD)


Here, the new new style definition completely replaces the style definition
contained in the Sphinx style sheet. It is also possible to override only part
of the style definition. The following style definition changes only the item
spacing between enumerated list items. All other style properties (such as the
left margin and the item numbering format) remain unchanged.


.. code-block:: python

    my_style_sheet('enumerated list', base=styles['default'],
                   flowable_spacing=3*PT)



Starting with a clean slate
...........................

Instantiating a new style sheet without passing it a base style sheet creates
an independent style sheet. You need to specify the :class:`StyledMatcher` to
use in this case.

.. code-block:: python

    from rinoh.dimension import PT
    from rinoh.font.style import BOLD
    from rinohlib.stylesheets.sphinx import styles
    from rinohlib.stylesheets.matcher import matcher

    independent_style_sheet = StyleSheet('My Independent Style Sheet',
                                         matcher=matcher)


If a style definition for a particular document element is missing, the default
values for its style properties are used.


Documument Templates
~~~~~~~~~~~~~~~~~~~~

As with style sheets, you can choose to make use of the templates provided by
RinohType or you can create a custom template from scratch. This section only
covers the former. For an example of how to create a custom template, see the
invoice example.

RinohType includes two document templates; :class:`Article` and :class:`Book`.
Theese templates can be customized by passing an :class:`ArticleOptions` or
:class:`BookOptions` instance as `options` on template instantiation
respectively. Both these classes derive from :class:`DocumentOptions` and thus
accept the options offered by it:

.. autoclass:: rinohlib.templates.base.DocumentOptions
    :members:


The :class:`Article` and :class:`Book` templates also have some specific
options:

.. autoclass:: rinohlib.templates.article.ArticleOptions
    :members:


.. autoclass:: rinohlib.templates.book.BookOptions
    :members:


.. [1] This will be configurable in the future.
