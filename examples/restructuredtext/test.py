from rinoh.backend import pdf
from rinoh.dimension import CM
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.structure import AdmonitionTitles
from rinoh.stylesheets import sphinx
from rinoh.template import DocumentOptions
from rinoh.templates import Article


if __name__ == '__main__':
    strings = (AdmonitionTitles(important='IMPORTANT:',
                                tip='TIP:'),
               )

    configuration = Article.Configuration()
    configuration.abstract_location('title')
    configuration.table_of_contents(False)
    configuration.title_page(top_margin=2 * CM)

    for name in ('demo', 'quickstart', 'FAQ', 'THANKS'):
        parser = ReStructuredTextReader()
        with open(name + '.txt') as file:
            flowables = parser.parse(file)
        doc_options = DocumentOptions(stylesheet=sphinx)
        document = Article(flowables, strings=strings,
                           configuration=configuration,
                           options=doc_options, backend=pdf)
        document.render(name)
