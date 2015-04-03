from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextParser

from rinohlib.stylesheets.somestyle import stylesheet as STYLESHEET
from rinohlib.templates.book import Book, BookOptions
from rinohlib.templates.article import Article

if __name__ == '__main__':
#    for name in ('quickstart', 'FAQ', 'THANKS'):
    for name in ('demo', ):
        parser = ReStructuredTextParser()
        document_tree = parser.parse(name + '.txt')
        # manual_options = BookOptions(stylesheet=STYLESHEET)
        # document = Book(document_tree, options=manual_options, backend=pdf)
        document = Article(document_tree, backend=pdf)
        document.render(name)
