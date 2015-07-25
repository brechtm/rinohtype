from rinoh.paper import A5
from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextParser

from rinohlib.stylesheets.somestyle import stylesheet as STYLESHEET
from rinohlib.templates.book import Book, BookOptions
from rinohlib.templates.article import Article, ArticleOptions

if __name__ == '__main__':
   for name in ('quickstart', 'FAQ', 'THANKS'):
#     for name in ('demo', ):
        parser = ReStructuredTextParser()
        flowables = parser.parse(name + '.txt')
        # manual_options = BookOptions(stylesheet=STYLESHEET)
        # document = Book(document_tree, options=manual_options, backend=pdf)
        article_options = ArticleOptions(table_of_contents=False, page_size=A5)
        document = Article(flowables, options=article_options, backend=pdf)
        document.render(name)
