from pathlib import Path

from rinoh import register_template
from rinoh.attribute import OverrideDefault, Var
from rinoh.dimension import CM
from rinoh.image import Image
from rinoh.stylesheets import sphinx_article
from rinoh.template import (DocumentTemplate, ContentsPartTemplate,
                            PageTemplate, DocumentPartTemplate,
                            FixedDocumentPartTemplate)

from . page import MyTitlePageTemplate


class MyTitlePartTemplate(DocumentPartTemplate):
    drop_if_empty = OverrideDefault(False)

    def _flowables(self, document):
        return iter([])


class MyDocumentTemplate(DocumentTemplate):
    identifier = 'my_document_template'

    stylesheet = OverrideDefault(sphinx_article)

    parts = OverrideDefault(['title', 'front_matter', 'contents'])

    # default document part templates
    title = MyTitlePartTemplate()
    front_matter = FixedDocumentPartTemplate()
    contents = ContentsPartTemplate()

    # default page templates
    page = PageTemplate(page_size=Var('paper_size'))
    title_page = MyTitlePageTemplate(base='page', top_margin=8*CM)
    front_matter_page = PageTemplate(base='page')
    contents_page = PageTemplate(base='page')

    TEMPLATE_IMAGE = Image(Path(__file__).parent / 'template.png')


# TODO: the following is better!
register_template('my_document_template', MyDocumentTemplate)
# TODO: even better: 'identifier' attribute in class
