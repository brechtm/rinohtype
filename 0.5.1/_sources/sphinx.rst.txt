.. _sphinx_builder:

Sphinx Builder
==============

:mod:`rinoh.frontent.sphinx` is a Sphinx extension module. It provides a Sphinx
builder with the name *rinoh*. The builder recognizes the following ``conf.py``
options. Of these, only :confval:`rinoh_documents` (or
:confval:`sphinx:latex_documents`) is required.

.. confval:: rinoh_documents

    Determines which PDF documents to build. Its format is a list of
    dictionaries, one for each document to be generated. The supported keys
    for these dictionaries are listed below. Two of them are required:

    doc (required)
        String that specifies the name of the master document (typically
        ``index``).

    target (required)
        The name of the target PDF file without the extension.

    The following keys allow overriding the content included on the document's
    title page and page headers/footers (depending on the template and its
    configuration). The values for text content can be plain text or
    :class:`~.StyledText`.

    logo (no default)
        Path (absolute or relative to the location of the ``conf.py`` file) to
        an image file, typically included on the title page.

    title (default: ":confval:`sphinx:project` documentation")
        The title of the document.

    subtitle (default: "Release :confval:`sphinx:release`")
        Subtitle of the document.

    author (default: ":confval:`sphinx:author`")
        The document's author.

    date (default: determined from :confval:`sphinx:today` and :confval:`sphinx:today_fmt`)
        The document (build) date.

    The remaining keys control what is included in the document and the
    document template (configuration) to use.

    toctree_only (default: ``False``)
        Must be ``True`` or ``False``. If true, the document itself is not
        included in the output, only the documents referenced by it via TOC
        trees.

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
          (see :option:`rinoh --list-templates`), or
        * a :class:`.DocumentTemplate` subclass

    *rinoh_documents* will also accept other keys than those listed above.
    These items will be available as document metadata and can be used in a
    :ref:`custom document template <custom-template>`.

    Example::

        rinoh_documents = [
            dict(doc='index', target='manual', toctree_only=False,
                 template='manual.rtt', logo='logo.pdf'),
            dict(doc='ref', target='reference', title='Reference Manual',
                 template='reference.rtt', stamp='DRAFT'),
        ]


Legacy Configuration Variables
------------------------------

The configuration variables below are no longer supported. Instead, their
functionality can now be configured per document in :confval:`rinoh_documents`.

.. confval:: rinoh_template

    This configuration variable is **no longer supported** since the
    document template can be specified in :confval:`rinoh_documents` entries.


.. confval:: rinoh_stylesheet

    This configuration variable is **no longer supported** since it is not
    obvious which style sheet will be used when the template configuration also
    specifies a style sheet. Please specify the style sheet to use in your
    :ref:`template configuration file <configure_templates>`:

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

    This configuration variable is **no longer supported** since the logo can
    be specified in the :confval:`rinoh_documents` entries.

.. confval:: rinoh_domain_indices

    This configuration variable is **no longer supported** since the
    domain_indices can be specified in the :confval:`rinoh_documents` entries.

.. confval:: rinoh_metadata

    This configuration variable is **no longer supported**. Metadata entries
    can now be added to :confval:`rinoh_documents` entries.
