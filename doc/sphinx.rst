.. _sphinx_builder:

Sphinx Builder
==============

:mod:`rinoh.frontent.sphinx` is a Sphinx extension module. It provides a Sphinx
builder with the name *rinoh*. The builder recognizes the following ``conf.py``
options. Of these, only :confval:`rinoh_documents` (or
:confval:`sphinx:latex_documents`) is required.

Note that

.. confval:: rinoh_documents

    Determines how to group the document tree into PDF output files. Its format
    is identical to that of :confval:`sphinx:latex_documents`, with the
    exception that `targetname` should specify the name of the PDF file without
    the extension. If it is not specified, the value of
    :confval:`sphinx:latex_documents` is used instead (with the ``.tex``
    extension stripped from the `targetname`).

.. confval:: rinoh_template

    Determines the template used to render the document. It takes:

    * the filename of a :ref:`template configuration file <configure_templates>`,
    * a :class:`.TemplateConfiguration` instance,
    * the name of an installed template (see :option:`rinoh --list-templates`)
    * a :class:`.DocumentTemplate` subclass

    The default is ``'book'``, which resolves to the :class:`.Book` template.

.. confval:: rinoh_stylesheet

    This configuration variable is **no longer supported** since it was not
    obvious which style sheet was being used when the template configuration
    (:confval:`rinoh_template`) also specified a style sheet. Please specify
    the style sheet to use in your :ref:`template configuration file
    <configure_templates>`:

    .. code-block:: ini

        [TEMPLATE_CONFIGURATION]
        name = My Book
        template = book
        stylesheet = my_stylesheet.rts

.. confval:: rinoh_paper_size

    This configuration variable is **no longer supported** since it was not
    obvious which paper size was being used when the template configuration
    (:confval:`rinoh_template`) also specified a paper size. Please specify
    the paper_size to use in your :ref:`template configuration file
    <configure_templates>`:

    .. code-block:: ini

        [TEMPLATE_CONFIGURATION]
        name = My Book
        template = book

        [VARIABLES]
        paper_size = A5

.. confval:: rinoh_logo

    Path (relative to the configuration directory) to an image file to use at
    the top of the title page. If not specified, the
    :confval:`sphinx:latex_logo` value is used.

.. confval:: rinoh_domain_indices

    Controls the generation of domain-specific indices. Identical to
    :confval:`sphinx:latex_domain_indices`, which is used when
    :confval:`rinoh_domain_indices` is not specified.

.. confval:: rinoh_metadata

    A dictionary instance that provides additional configuration values to the
    document template, typically used on the title page and in page headers and
    footers (depending on the template and its configuration). The values
    supplied can be plain text or :class:`~.StyledText`. They are normally
    derived from other Sphinx configuration variables, but it can be useful to
    override them for PDF output. Supported keys:

    title
        Overrides :confval:`sphinx:project`
    subtitle
        Overrides the default Sphinx subtitle containing the project's
        :confval:`sphinx:release` string
    author
        Overrides :confval:`sphinx:author`
    date
        Overrides the default date determined from :confval:`sphinx:today` and
        :confval:`sphinx:today_fmt`
