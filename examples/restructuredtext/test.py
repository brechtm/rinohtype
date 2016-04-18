from rinoh.dimension import CM
from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.structure import TableOfContentsSection, AdmonitionTitles
from rinoh.stylesheets import sphinx
from rinoh.template import (DocumentOptions, DocumentTemplate, PageTemplate,
                            TitlePageTemplate, ContentsPartTemplate,
                            FixedDocumentPartTemplate)

if __name__ == '__main__':
    title_page_template = TitlePageTemplate(top_margin=8*CM)
    page_template = PageTemplate()
    document_parts = [FixedDocumentPartTemplate(title_page_template),
                      FixedDocumentPartTemplate(page_template,
                                                [TableOfContentsSection()]),
                      ContentsPartTemplate(page_template)]

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
        document = DocumentTemplate(flowables, document_parts, strings=strings,
                                    options=doc_options, backend=pdf)
        document.render(name)
