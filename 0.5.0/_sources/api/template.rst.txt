.. module:: rinoh.template

.. _template:

Templates (:mod:`rinoh.template`)
=================================

Document templates are created by subclassing :class:`DocumentTemplate`, just
like the :ref:`standard templates <standard_templates>` shipped with rinohtype.

.. autoclass:: DocumentTemplate
    :members:


Document templates can be customized by setting values for the configuration
attributes defined in a :class:`DocumentTemplate` subclass in a
:class:`TemplateConfiguration`. An template configuration can be passed as
*configuration* on template instantiation. However, it is better to make use of
the :class:`~TemplateConfiguration.document` method, however.

.. autoclass:: TemplateConfiguration
    :members:

.. autoclass:: PartsList
    :members:


Document Parts
~~~~~~~~~~~~~~

.. autoclass:: DocumentPart
    :members:


The document part templates which are listed by name in
:attr:`DocumentTemplate.parts` are looked up as attributes of the
:class:`DocumentTemplate` subclass. They are instances of
:class:`DocumentPartTemplate` subclasses:

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
