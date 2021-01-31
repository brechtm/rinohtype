.. _sphinx_builder:

Sphinx Builder
==============

:mod:`rinoh.frontent.sphinx` is a Sphinx extension module. It provides a Sphinx
builder with the name *rinoh*. The builder recognizes the following ``conf.py``
options. Of these, only :confval:`rinoh_documents` (or
:confval:`sphinx:latex_documents`) is required.

.. confval:: rinoh_documents

    Determines which PDF documents to build. Its format is a list of
    dictionaries, one for each document to be generated. Supported keys are:

    doc (required)
        String that specifies the name of the master document (typically
        ``index``).
    target (required)
        The name of the target PDF file without the extension.
    title (required)
        The title of the document.
    author (required)
        The author of the document.
    toctree_only (default: ``False``)
        Must be ``True`` or ``False``. If true, the document itself is not
        included in the output, only the documents referenced by it via TOC
        trees.
    logo (default: ``None``)
        Path (relative to the configuration directory) to an image file to use
        at the top of the title page.
    domain_indices (default: ``True``)
        If true, generate domain-specific indices in addition to the general
        index. It is equivalent to the :confval:`sphinx:html_domain_indices`
        and :confval:`sphinx:latex_domain_indices` configuration variables.
    template (default: :class:`.Book`)
        Determines the template used to render the document. It takes:

        * the filename of a :ref:`template configuration file
          <configure_templates>`,
        * a :class:`.TemplateConfiguration` instance,
        * the name of an installed template
          (see :option:`rinoh --list-templates`)
        * a :class:`.DocumentTemplate` subclass


.. confval:: rinoh_template

    This configuration variable is **no longer supported** since the
    document template can be specified in :confval:`rinoh_documents`.


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

.. note:: For some of the configuration variables listed below, rinohtype used
    to fall back to the corresponding variable for the LaTeX builder. This
    behavior was removed to make the configuration more transparent. Make sure
    to set the rinoh variables if you relied on this.

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

    This configuration variable is **no longer supported** since the logo can
    be specified in the :confval:`rinoh_documents`.

.. confval:: rinoh_domain_indices

    This configuration variable is **no longer supported** since the
    domain_indices can be specified in the :confval:`rinoh_documents`.

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
