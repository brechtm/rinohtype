
from rinoh.document import DocumentPart, Page, DocumentSection
from rinoh.layout import Container
from rinoh.paragraph import Paragraph

from .base import (DocumentBase, DocumentOptions,
                   TableOfContentsPart, ContentsPart)


# page definitions
# ----------------------------------------------------------------------------

class TitlePage(Page):
    def __init__(self, document_part, paper, orientation):
        super().__init__(document_part, paper, orientation)
        h_margin = self.document.options['page_horizontal_margin']
        v_margin = self.document.options['page_vertical_margin']
        body_width = self.width - (2 * h_margin)
        body_height = self.height - (2 * v_margin)
        title_top = self.height / 4
        self.title = Container('title', self, h_margin, title_top,
                               body_width, body_height)
        self.title << Paragraph(self.document.metadata['title'],
                                style='title page title')
        if 'subtitle' in self.document.metadata:
            self.title << Paragraph(self.document.metadata['subtitle'],
                                    style='title page subtitle')
        if 'author' in self.document.metadata:
            self.title << Paragraph(self.document.metadata['author'],
                                    style='title page author')
        date = self.document.metadata['date']
        try:
            self.title << Paragraph(date.strftime('%B %d, %Y'),
                                    style='title page date')
        except AttributeError:
            self.title << Paragraph(date, style='title page date')
        extra = self.document.options['extra']
        if extra:
            self.title << Paragraph(extra, style='title page extra')


# document parts
# ----------------------------------------------------------------------------

class TitlePart(DocumentPart):
    def init(self):
        self.add_page(self.new_page(None))

    def new_page(self, chains):
        assert chains is None
        return TitlePage(self, self.document.options['page_size'],
                         self.document.options['page_orientation'])


class FrontMatter(DocumentSection):
    parts = [TitlePart, TableOfContentsPart]


class BodyMatter(DocumentSection):
    parts = [ContentsPart]


# main document
# ----------------------------------------------------------------------------

class BookOptions(DocumentOptions):
    options = {'extra': None}


class Book(DocumentBase):
    sections = [FrontMatter, BodyMatter]
    options_class = BookOptions
