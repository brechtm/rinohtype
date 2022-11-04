from pathlib import Path

from rinoh import register_template
from rinoh.attribute import OverrideDefault, Var
from rinoh.dimension import CM, PT
from rinoh.image import Image
from rinoh.layout import DownExpandingContainer, CONTENT, UpExpandingContainer
from rinoh.paragraph import Paragraph
from rinoh.stylesheets import sphinx_article
from rinoh.template import (DocumentTemplate, ContentsPartTemplate,
                            BodyPageTemplate, DocumentPartTemplate,
                            FixedDocumentPartTemplate, PageBase, PageTemplateBase)
from rinoh.text import StyledText

from . page import MyTitlePageTemplate


class MyTitlePartTemplate(DocumentPartTemplate):
    drop_if_empty = OverrideDefault(False)

    def _flowables(self, document):
        return iter([])


class RearCoverPageTemplate(PageTemplateBase):
    def page(self, document_part, page_number, chain):
        return RearCoverPage(document_part, self, page_number)


REAR_COVER_PAGE_TEXT = r"""
'Some '(style 1) 'Text\n'(style 2)
'Some '(style 1) 'Text'(style 2)
""".replace('\n', '') # work around rinohtype bug


class RearCoverPage(PageBase):
    configuration_class = RearCoverPageTemplate

    def __init__(self, document_part, template, page_number):
        super().__init__(document_part, template, page_number)
        margin = 2*CM
        split = 20*CM
        width = self.width - 2 * margin
        self.text = UpExpandingContainer('text', CONTENT, self, left=margin,
                                         bottom=split, width=width)
        self.text << Paragraph(StyledText.from_string(REAR_COVER_PAGE_TEXT),
                               style='rear cover page text')
        self.imgs = DownExpandingContainer('images', CONTENT, self,
                                           left=margin, top=split, width=width)
        self.imgs << Image(Path(__file__).parent / 'template.png',
                           width=2*CM, align='right')


class RearCoverPartTemplate(DocumentPartTemplate):
    drop_if_empty = OverrideDefault(False)

    def _flowables(self, document):
        return iter([])     # content is static, placed in RearCoverPage


class MyDocumentTemplate(DocumentTemplate):
    identifier = 'my_document_template'

    stylesheet = OverrideDefault(sphinx_article)

    parts = OverrideDefault(['title', 'front_matter', 'contents', 'rear_cover'])

    # default document part templates
    title = MyTitlePartTemplate()
    front_matter = FixedDocumentPartTemplate(page_number_format='continue')
    contents = ContentsPartTemplate(page_number_format='continue')
    rear_cover = RearCoverPartTemplate()

    # default page templates
    page = BodyPageTemplate(page_size=Var('paper_size'))
    title_page = MyTitlePageTemplate(base='page', top_margin=8*CM)
    front_matter_page = BodyPageTemplate(base='page')
    contents_page = BodyPageTemplate(base='page')
    rear_cover_page = RearCoverPageTemplate(base='page')

    TEMPLATE_IMAGE = Image(Path(__file__).parent / 'template.png')


# TODO: the following is better!
register_template('my_document_template', MyDocumentTemplate)
# TODO: even better: 'identifier' attribute in class
