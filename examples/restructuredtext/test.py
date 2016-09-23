from rinoh.backend import pdf
from rinoh.dimension import CM
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.strings import Strings
from rinoh.structure import AdmonitionTitles
from rinoh.stylesheets import sphinx_article
from rinoh.templates import Article


if __name__ == '__main__':
    strings = Strings(AdmonitionTitles(important='IMPORTANT:',
                                       tip='TIP:'))

    configuration = Article.ConfigurationFile('article.rtt')

    for name in ('demo', 'quickstart', 'FAQ', 'THANKS'):
        parser = ReStructuredTextReader()
        with open(name + '.txt') as file:
            document_tree = parser.parse(file)
        document = Article(document_tree, configuration=configuration)
        document.render(name)
