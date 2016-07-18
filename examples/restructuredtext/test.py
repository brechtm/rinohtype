from rinoh.backend import pdf
from rinoh.dimension import CM
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.structure import AdmonitionTitles
from rinoh.stylesheets import sphinx_article
from rinoh.templates import Article


if __name__ == '__main__':
    strings = (AdmonitionTitles(important='IMPORTANT:',
                                tip='TIP:'),
               )

    configuration = Article.Configuration(stylesheet=sphinx_article,
                                          abstract_location='title',
                                          table_of_contents=False)
    configuration('title_page', top_margin=2 * CM)

    for name in ('demo', 'quickstart', 'FAQ', 'THANKS'):
        parser = ReStructuredTextReader()
        with open(name + '.txt') as file:
            flowables = parser.parse(file)
        document = Article(flowables, strings=strings,
                           configuration=configuration, backend=pdf)
        document.render(name)
