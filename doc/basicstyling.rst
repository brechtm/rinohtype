.. _basic_styling:

Basic Document Styling
======================

rinohtype allows for fine-grained control over the style of its output. Most
aspects of a document's style can be controlled by style sheet files and
template configuration files which are being introduced in this chapter. These
files are plain text files that are easy to create, read and modify.


.. _basics_stylesheets:

Style Sheets
~~~~~~~~~~~~

.. currentmodule:: rinoh.style

A style sheet defines the look of each element in a document. For each type of
document element, the style sheet assign values to the style properties
available for that element. Style sheets are stored in plain text files using
the Windows INI\ [#ini]_ format with the ``.rts`` extension. Below is an
excerpt from the :doc:`sphinx_stylesheet` included with rinohtype.

.. _base style sheet:

.. literalinclude:: /../src/rinoh/data/stylesheets/sphinx.rts
    :language: ini
    :end-before: [italic]

Except for ``[STYLESHEET]`` and ``[VARIABLES]``, each configuration section
in a style sheet determines the style of a particular type of document element.
The ``emphasis`` style, for example, determines the look of emphasized text,
which is displayed in an italic font. This is similar to how HTML's cascading
style sheets work. In rinohtype however, document elements are identified by
means of a descriptive label (such as *emphasis*) instead of a cryptic
selector. rinohtype also makes use of selectors, but these are collected in a
:ref:`matcher <matchers>` which maps them to descriptive names to be used by
many style sheets. Unless you are using rinohtype as a PDF library to create
custom documents, the :ref:`default matcher <default_matcher>` should cover
your needs.

The following two subsections illustrate how to extend an existing style sheet
and how to create a new, independent style sheet. For more in-depth information
on style sheets, please refer to :ref:`styling`.


Extending an Existing Style Sheet
---------------------------------

Starting from an existing style sheet, it is easy to make small changes to the
style of individual document elements. The following style sheet file is based
on the Sphinx stylesheet included with rinohtype.

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
italic font (as configured in the `base style sheet`_) and colored blue
(``#00a``).

It is also possible to completely override a style definition. This can be done
by setting the ``base`` of a style definition to ``DEFAULT_STYLE`` as
illustrated by the `strong` style. This causes strongly emphasised text to be
displayed in red (#a00) but **not** in a bold font as was defined in the `base
style sheet`_ (the default for ``font_weight`` is `Medium`; see
:class:`~rinoh.text.TextStyle`). Refer to :ref:`default_matcher` to find out
which style attributes are accepted by each style (by following the hyperlink
to the style class's documentation).

The style sheet also redefines the ``mono_typeface`` variable. This variable is
used in the `base style sheet`_ in all style definitions where a monospaced
font is desired. Redefining the variable in the derived style sheet affects
all of these style definitions.


Starting from Scratch
---------------------

If you don't specify a base style sheet in the ``[STYLESHEET]`` section, you
create an independent style sheet. You should do this if you want to create
a document style that is not based on an existing style sheet. If the style
definition for a particular document element is not included in the style
sheet, the default values for its style properties are used.

.. todo:: specifying a custom matcher for an INI style sheet

    Unless a custom :class:`StyledMatcher` is passed to
    :class:`StyleSheetFile`, the :ref:`default matcher <default_matcher>` is
    used. Providing your own matcher offers even more customizability, but it
    is unlikely you will need this. See :ref:`matchers`.

.. note:: In the future, rinohtype will be able to generate an empty INI style
    sheet, listing all styles defined in the matcher with the supported style
    attributes along with the default values as comments. This generated style
    sheet can serve as a good starting point for developing a custom style
    sheet from scratch.


.. _basics_templates:

Document Templates
~~~~~~~~~~~~~~~~~~

As with style sheets, you can choose to make use of a template provided by
rinohtype and optionally customize it or you can create a custom template from
scratch. This section discusses how you can configure an existing template. See
:ref:`templates` on how to create a custom template.


.. _configure_templates:

Configuring a Template
----------------------

rinohtype provides a number of :ref:`standard_templates`. These can be
customized by means of a template configuration file; a plain text file in the
INI\ [#ini]_ format with the ``.rtt`` extension. Here is an example
configuration for the article template:

.. literalinclude:: /my_article.rtt
    :language: ini

The ``TEMPLATE_CONFIGURATION`` sections collects global template options. Set
*name* to provide a short label for your template configuration. *template*
identifies the :ref:`document template <standard_templates>` to configure.

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
configurable. Refer to :ref:`standard_templates` for details.

.. todo:: base for part template?


Using a Template Configuration File
-----------------------------------

A template configuration file can be specified when rendering using the
command-line :program:`rinoh` tool by passing it to the
:option:`--template <rinoh --template>` command-line option. When using the
:ref:`Sphinx_builder`, you can set the :confval:`rinoh_template` option in
``conf.py``.

To render a document using this template configuration programatically, load
the template file using :class:`.TemplateConfigurationFile`:

.. include:: testcode.rst

.. testcode:: my_document

    import sys
    from pathlib import Path

    from rinoh.frontend.rst import ReStructuredTextReader
    from rinoh.template import TemplateConfigurationFile

    # the parser builds a rinohtype document tree
    parser = ReStructuredTextReader()
    with open('my_document.rst') as file:
        document_tree = parser.parse(file)

    # load the article template configuration file
    script_path = Path(sys.path[0]).resolve()
    config = TemplateConfigurationFile(script_path / 'my_article.rtt')

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


.. footnotes

.. [#ini] see *Supported INI File Structure* in :mod:`python:configparser`
