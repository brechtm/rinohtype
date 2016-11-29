.. _templates:

Document Templates
==================

Customizing a Template
----------------------

If you need to customize a template beyond what is possible by configuration,
you can subclass the :class:`Article` (or other) template class and extend it,
or override document part and page templates with custom templates.

.. testcode:: subclass_article

    from rinoh.attribute import OverrideDefault
    from rinoh.template import DocumentPartTemplate, PageTemplate
    from rinoh.templates import Article


    class BibliographyPartTemplate(DocumentPartTemplate):
        ...


    class MyTitlePageTemplate(PageTemplate):
        ...


    class MyArticle(Article):
        parts = OverrideDefault(['title', 'contents', 'bibliography'])

        # default document part templates
        bibliography = BibliographyPartTemplate()

        # default page templates
        title_page = MyTitlePageTemplate(base='page')
        bibliography_page = PageTemplate(base='page')


:class:`MyArticle` extends the :class:`.Article` template, adding the extra
:attr:`~.MyArticle.bibliography` document part, along with the page template
:attr:`~.MyArticle.bibliography_page`. The new document part is included in
:attr:`~.DocumentTemplate.parts`, while also leaving out
:attr:`~.Article.front_matter` by default. Finally, the template also replaces
the title page template with a custom one.


Creating a Custom Template
--------------------------

A new template can be created from scratch by subclassing
:class:`DocumentTemplate`, defining all document parts, their templates and
page templates.

The :class:`.Article` and :class:`.Book` templates are examples of templates
that inherit directly from :class:`DocumentTemplate`. We will briefly discuss
the article template here. The :class:`.Article` template overrides the default
style sheet and defines the two custom template attributes discussed in
:ref:`configure_templates`. The document parts :attr:`~.Article.title`,
:attr:`~.Article.front_matter` and :attr:`~.Article.contents` are listed the in
:attr:`~.Article.parts` attribute and templates for each of them are provided
along with page templates:

.. literalinclude:: /../src/rinoh/templates/article.py
    :pyobject: Article

The custom :class:`.ArticleFrontMatter` template reads the values for the
two custom template attributes defined in :class:`.Article` to determine which
flowables are included in the front matter:

.. literalinclude:: /../src/rinoh/templates/article.py
    :pyobject: ArticleFrontMatter

Have a look at the :doc:`src/book` for an example of a slightly more complex
template that defines separate templates for left and right pages.
