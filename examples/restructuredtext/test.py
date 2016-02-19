from rinoh.paper import A5
from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.style import StyleSheetFile
from rinoh.template import DocumentOptions, DocumentTemplate

from rinohlib.stylesheets.somestyle import stylesheet as STYLESHEET
from rinohlib.templates.base import SimplePage, ContentsPart
from rinohlib.templates.book import Book, BookOptions
from rinohlib.templates.article import Article, ArticleOptions
from rinohlib.stylesheets.matcher import matcher

if __name__ == '__main__':
    sphinx_stylesheet = StyleSheetFile('sphinx.rts', matcher)

    page_template = SimplePage
    document_parts = [#(TitlePart, page_template, True),
                      #(FrontMatterPart, page_template, [TableOfContentsSection()]),
                      (ContentsPart, page_template, False)]


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
