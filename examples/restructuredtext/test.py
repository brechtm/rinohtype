from rinoh.dimension import CM
from rinoh.paper import A5
from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.structure import TableOfContentsSection
from rinoh.style import StyleSheetFile
from rinoh.template import (DocumentOptions, DocumentTemplate, PageTemplate,
                            TitlePageTemplate)

from rinohlib.stylesheets.somestyle import stylesheet as STYLESHEET
from rinohlib.templates.base import (SimplePage, ContentsPartTemplate,
                                     FixedDocumentPartTemplate)
from rinohlib.templates.book import Book, BookOptions
from rinohlib.templates.article import Article, ArticleOptions
from rinohlib.stylesheets.matcher import matcher

if __name__ == '__main__':
    sphinx_stylesheet = StyleSheetFile('sphinx.rts', matcher)

    title_page_template = TitlePageTemplate(top_margin=8*CM)
    page_template = PageTemplate()
    document_parts = [FixedDocumentPartTemplate(title_page_template, []),
                      FixedDocumentPartTemplate(page_template,
                                                [TableOfContentsSection()]),
                      ContentsPartTemplate(page_template, False)]


    for name in ('demo', 'quickstart', 'FAQ', 'THANKS'):
        parser = ReStructuredTextReader()
        with open(name + '.txt') as file:
            flowables = parser.parse(file)
        # manual_options = BookOptions(stylesheet=STYLESHEET)
        # document = Book(document_tree, options=manual_options, backend=pdf)
        doc_options = DocumentOptions(stylesheet=sphinx_stylesheet)
        document = DocumentTemplate(flowables, document_parts,
                                    options=doc_options, backend=pdf)
        document.render(name)
