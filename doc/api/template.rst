.. module:: rinoh.template

.. _template:

Templates
=========

The standard templates shipped with rinohtype all inherit from
:class:`DocumentTemplate`:

.. autoclass:: DocumentTemplate
    :members:
    :inherited-members:

Customization of the templates is performed by passing an instance of the
template-specific :class:`TemplateConfiguration` subclass as *configuration*
on template instantiation.

.. autoclass:: TemplateConfiguration
    :members:


Document Parts
~~~~~~~~~~~~~~

The document part templates of which instances are include in
:attr:`DocumentTemplate.parts` implement this interface:

.. autoclass:: DocumentPartTemplate
    :members:


The following document part templates are used in the standard document
templates:

.. autoclass:: TitlePartTemplate
    :members:

.. autoclass:: ContentsPartTemplate
    :members:

.. autoclass:: FixedDocumentPartTemplate
    :members:


Page Templates
~~~~~~~~~~~~~~

The document templates make use of page templates:

.. autoclass:: PageTemplate
    :members:

.. autoclass:: TitlePageTemplate
    :members:


The base class for these collects the common options:

.. autoclass:: PageTemplateBase
    :members:
