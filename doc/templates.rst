.. _document_templates:

.. module:: rinoh.template

Standard Document Templates
===========================

Rinohtype includes the following document templates:

.. toctree::

    article
    book


These are configurable and therefor should cater for most documents. The
templates inherit from :class:`DocumentTemplate`.

.. autoclass:: DocumentTemplate
    :members:
    :inherited-members:

The document part templates should implement the following interface:

.. autoclass:: DocumentPartTemplate
    :members:

Customization of the templates is performed by passing an instance of the
template-specific :class:`TemplateConfiguration` subclass as *configuration*
on template instantiation.

.. autoclass:: TemplateConfiguration
    :members:


The document templates make use of page templates:

.. autoclass:: PageTemplate
    :show-inheritance:
    :members:

.. autoclass:: TitlePageTemplate
    :show-inheritance:
    :members:


The base class for these collects the common options:

.. autoclass:: PageTemplateBase
    :show-inheritance:
    :members:
