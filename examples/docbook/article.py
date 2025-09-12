
from rinoh.frontend.docbook import DocBookReader
from rinoh.templates.article import Article


if __name__ == '__main__':
    reader = DocBookReader()
    for name in ('sequence', 'article_db50', 'article_db45'):
        with open(name + '.xml') as file:
            flowables = reader.parse(file)
        document = Article(flowables)
        document.render(name)
