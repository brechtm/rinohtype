from rinoh.paper import A5
from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextReader

from rinohlib.stylesheets.somestyle import stylesheet as STYLESHEET
from rinohlib.templates.book import Book, BookOptions
from rinohlib.templates.article import Article, ArticleOptions

if __name__ == '__main__':
    for name in ('quickstart', 'demo', 'FAQ', 'THANKS'):
        parser = ReStructuredTextReader()
        with open(name + '.txt') as file:
            flowables = parser.parse(file)
        # manual_options = BookOptions(stylesheet=STYLESHEET)
        # document = Book(document_tree, options=manual_options, backend=pdf)
        article_options = ArticleOptions(table_of_contents=False, page_size=A5)
        document = Article(flowables, options=article_options, backend=pdf)
        document.render(name)
