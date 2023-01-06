from pathlib import Path

from rinoh import register_template
from rinoh.attribute import OverrideDefault
from rinoh.dimension import CM
from rinoh.image import Image
from rinoh.layout import CONTENT, DownExpandingContainer, UpExpandingContainer
from rinoh.paragraph import Paragraph
from rinoh.template import DocumentPartTemplate, PageBase, PageTemplateBase
from rinoh.templates import Book
from rinoh.text import StyledText


class RearCoverPageTemplate(PageTemplateBase):
    def page(self, document_part, page_number, chain):
        return RearCoverPage(document_part, self, page_number)


REAR_COVER_PAGE_TEXT = r"""
'Some '(rear cover small) 'Text\n'(rear cover large)
'Some '(rear cover large) 'Text'(rear cover small)
"""


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
        self.imgs << Image(Path(__file__).parent / 'rear_page_1.png',
                           width=2*CM, align='right')
        self.imgs << Image(Path(__file__).parent / 'rear_page_2.png',
                           width=2*CM, align='right')


class RearCoverPartTemplate(DocumentPartTemplate):
    drop_if_empty = OverrideDefault(False)

    def _flowables(self, document):
        return iter([])     # content is static, placed in RearCoverPage


class MyDocumentTemplate(Book):
    parts = OverrideDefault(['title', 'front_matter', 'contents', 'back_matter',
                             'rear_cover'])
    rear_cover = RearCoverPartTemplate()
    rear_cover_page = RearCoverPageTemplate(base='page')


register_template('my_template', MyDocumentTemplate)
