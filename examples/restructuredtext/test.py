from rinoh.paper import A5
from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.style import StyleSheetFile

from rinohlib.stylesheets.somestyle import stylesheet as STYLESHEET
from rinohlib.templates.book import Book, BookOptions
from rinohlib.templates.article import Article, ArticleOptions
from rinohlib.stylesheets.matcher import matcher

if __name__ == '__main__':
    for name in ('quickstart', 'demo', 'FAQ', 'THANKS'):
    sphinx_stylesheet = StyleSheetFile('sphinx.rts', matcher)

        parser = ReStructuredTextReader()
        with open(name + '.txt') as file:
            flowables = parser.parse(file)
        # manual_options = BookOptions(stylesheet=STYLESHEET)
        # document = Book(document_tree, options=manual_options, backend=pdf)
        article_options = ArticleOptions(table_of_contents=True, page_size=A5,
                                         stylesheet=sphinx_stylesheet)
        document = Article(flowables, options=article_options, backend=pdf)
        document.render(name)
