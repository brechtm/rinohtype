.. _templates:

Document Templates
==================

When it is not possible to achieve a particular document style using one of the
existing templates and a custom template configuration, you can create a new
template. A new template is programmed in Python and therefore it is required
that you are familiar with Python, or at least with general object-oriented
programming.


Subclassing a Template
----------------------

If you need to customize a template beyond what is possible by configuration,
you can subclass a template class and override document part and page templates
with custom templates. The following example subclasses :class:`.Article`.

.. testcode:: subclass_article

    from rinoh.attribute import OverrideDefault
    from rinoh.template import DocumentPartTemplate, BodyPageTemplate
    from rinoh.templates import Article


    class BibliographyPartTemplate(DocumentPartTemplate):
        ...


    class MyArticle(Article):
        parts = OverrideDefault(['contents', 'bibliography'])

        # default document part templates
        bibliography = BibliographyPartTemplate()

        # default page templates
        bibliography_page = BodyPageTemplate(base='page')


:class:`MyArticle` extends the :class:`.Article` template, adding the extra
:attr:`~.MyArticle.bibliography` document part, along with the page template
:attr:`~.MyArticle.bibliography_page`. The new document part is included in
:attr:`~.DocumentTemplate.parts`.


.. _custom-template:

Creating a Custom Template
--------------------------

A new template can be created from scratch by subclassing
:class:`.DocumentTemplate`, defining all document parts, their templates and
page templates.

The :class:`.Article` and :class:`.Book` templates are examples of templates
that inherit directly from :class:`.DocumentTemplate`. We will briefly discuss
the article template, the simpler of the two. The :class:`.Article` template
overrides the default style sheet and lists a single document
part named :attr:`~.Article.contents` in the :attr:`~.Article.parts` attribute
and provided a template for it are provided along with page templates:

.. literalinclude:: /../src/rinoh/templates/article.py
    :pyobject: Article

Have a look at the :doc:`src/book` for an example of a slightly more complex
template that defines separate templates for left and right pages.
