from rinoh.backend import pdf
from rinoh.frontend.commonmark import CommonMarkReader
from rinoh.templates import Article


if __name__ == '__main__':
    reader = CommonMarkReader()
    for name in ('README', ):
        with open(name + '.md', 'rb') as file:
            document_tree = reader.parse(file)
        document = Article(document_tree, backend=pdf)
        document.render(name)
