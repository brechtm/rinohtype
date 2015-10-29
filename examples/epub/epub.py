from rinoh.paper import A4
from rinoh.backend import pdf
from rinoh.frontend.epub import EPubReader

from rinohlib.templates.article import Article, ArticleOptions

if __name__ == '__main__':
    reader = EPubReader()
    with open('running_lean.epub', 'rb') as file:
        flowables = reader.parse(file)
    article_options = ArticleOptions(page_size=A4, table_of_contents=True)
    document = Article(flowables, options=article_options, backend=pdf)
    document.render('running_lean')
