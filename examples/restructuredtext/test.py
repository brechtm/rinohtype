from rinoh.dimension import CM
from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextReader
from rinoh.highlight import pygments_style_to_stylesheet
from rinoh.structure import TableOfContentsSection, AdmonitionTitles
from rinoh.stylesheets import sphinx
from rinoh.template import (DocumentOptions, DocumentTemplate, PageTemplate,
                            TitlePageTemplate, ContentsPartTemplate,
                            FixedDocumentPartTemplate)

if __name__ == '__main__':
    title_page_template = TitlePageTemplate(top_margin=8*CM)
    page_template = PageTemplate()
    document_parts = [FixedDocumentPartTemplate([], title_page_template),
                      FixedDocumentPartTemplate([TableOfContentsSection()],
                                                page_template),
                      ContentsPartTemplate(page_template)]

    strings = (AdmonitionTitles(important='IMPORTANT:',
                                tip='TIP:'),
               )

    try:
        from pygments.styles import get_style_by_name
        pygments_friendly = get_style_by_name('friendly')
        style_sheet = pygments_style_to_stylesheet(pygments_friendly)
        style_sheet.base = sphinx
    except ImportError:
        style_sheet = sphinx

    for name in ('demo', 'quickstart', 'FAQ', 'THANKS'):
        parser = ReStructuredTextReader()
        with open(name + '.txt') as file:
            flowables = parser.parse(file)
        # manual_options = BookOptions(stylesheet=STYLESHEET)
        # document = Book(document_tree, options=manual_options, backend=pdf)
        doc_options = DocumentOptions(stylesheet=style_sheet)
        document = DocumentTemplate(flowables, document_parts, strings=strings,
                                    options=doc_options, backend=pdf)
        document.render(name)
