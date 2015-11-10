from rinoh.paper import A4
from rinoh.backend import pdf
from rinoh.frontend.docbook import DocBookReader

from rinohlib.templates.article import Article, ArticleOptions

if __name__ == '__main__':
    reader = DocBookReader()
    for name in ('sequence', 'article_db50', 'article_db45'):
        with open(name + '.xml') as file:
            flowables = reader.parse(file)
        article_options = ArticleOptions(page_size=A4, table_of_contents=True)
        document = Article(flowables, options=article_options, backend=pdf)
        document.render(name)
