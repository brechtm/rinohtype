from pathlib import Path

from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.style import StyleSheet
from rinoh.template import TemplateConfigurationFile


DIR = Path(__file__).parent


if __name__ == '__main__':
    default_stylesheet = StyleSheet('empty')
    # default_stylesheet.write('emtpy')

    configuration = TemplateConfigurationFile(DIR / 'article.rtt')

    sphinx_stylesheet = configuration['stylesheet'].base
    # sphinx_stylesheet.write('sphinx')   # test writing an .rts stylesheet

    for name in ('demo', 'quickstart', 'FAQ', 'THANKS'):
        parser = ReStructuredTextReader()
        document_tree = parser.parse(name + '.txt')
        document = configuration.document(document_tree)
        document.render(name)