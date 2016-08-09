.. _sphinx_builder:

Sphinx Builder
--------------

The :mod:`rinoh.frontent.sphinx` is a Sphinx extension module. It provides a
Sphinx builder with the name *rinoh*.

The *rinoh* builder recognizes the following ``conf.py`` options. Of thse, only
:confval:`rinoh_documents` (or :confval:`sphinx:latex_documents`) needs to be
specified:

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
    installed template. For the latter, run :option:`rinoh --list-templates`
    to list the available templates. Default: ``'book'``.

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
