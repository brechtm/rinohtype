from rinoh.backend import pdf
from rinoh.dimension import CM
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.strings import Strings
from rinoh.structure import AdmonitionTitles
from rinoh.style import StyleSheet
from rinoh.stylesheets import sphinx_article
from rinoh.template import TemplateConfigurationFile


if __name__ == '__main__':
    default_stylesheet = StyleSheet('empty')
    default_stylesheet.write('emtpy')

    strings = Strings(AdmonitionTitles(important='IMPORTANT:',
                                       tip='TIP:'))

    configuration = TemplateConfigurationFile('article.rtt')

    sphinx_stylesheet = configuration['stylesheet'].base
    sphinx_stylesheet.write('sphinx')

    for name in ('demo', 'quickstart', 'FAQ', 'THANKS'):
        parser = ReStructuredTextReader()
        with open(name + '.txt') as file:
            document_tree = parser.parse(file)
        document = configuration.document(document_tree)
        document.render(name)
