from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextParser

from rinohlib.stylesheets.somestyle import stylesheet as STYLESHEET
from rinohlib.templates.manual import Manual, ManualOptions

if __name__ == '__main__':
#    for name in ('quickstart', 'FAQ', 'THANKS'):
    for name in ('optionlist', ):
        parser = ReStructuredTextParser()
        document_tree = parser.parse(name + '.txt')
        manual_options = ManualOptions(stylesheet=STYLESHEET)
        document = Manual(document_tree, options=manual_options, backend=pdf)
        document.render(name)
