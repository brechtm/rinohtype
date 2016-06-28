from rinoh.dimension import CM
from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.structure import TableOfContentsSection, AdmonitionTitles
from rinoh.stylesheets import sphinx
from rinoh.template import (DocumentOptions, DocumentTemplate, PageTemplate,
                            TitlePageTemplate, ContentsPartTemplate,
                            FixedDocumentPartTemplate)
from rinoh.templates import ArticleTemplate


if __name__ == '__main__':
    strings = (AdmonitionTitles(important='IMPORTANT:',
                                tip='TIP:'),
               )

    for name in ('demo', 'quickstart', 'FAQ', 'THANKS'):
        parser = ReStructuredTextReader()
        with open(name + '.txt') as file:
            flowables = parser.parse(file)
        # manual_options = BookOptions(stylesheet=STYLESHEET)
        # document = Book(document_tree, options=manual_options, backend=pdf)
        doc_options = DocumentOptions(stylesheet=sphinx)
        document = ArticleTemplate(flowables, strings=strings,
                                   options=doc_options, backend=pdf)
        document.render(name)
