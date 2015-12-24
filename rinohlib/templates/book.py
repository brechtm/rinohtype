
from rinoh.document import DocumentPart, Page, DocumentSection
from rinoh.layout import FlowablesContainer
from rinoh.number import ROMAN_LC
from rinoh.paragraph import Paragraph
from rinoh.reference import Variable, PAGE_NUMBER
from rinoh.text import MixedStyledText, Tab

from .base import (DocumentTemplate, DocumentOptions, Option, BookPart,
                   ContentsPart)


# page definitions
# ----------------------------------------------------------------------------

class TitlePage(Page):
    def __init__(self, document_part, paper, orientation):
        super().__init__(document_part, paper, orientation)
        options = self.document.options
        h_margin = options['page_horizontal_margin']
        v_margin = options['page_vertical_margin']
        body_width = self.width - (2 * h_margin)
        body_height = self.height - (2 * v_margin)
        title_top = self.height / 4
        self.title = FlowablesContainer('title', self, h_margin, title_top,
                                        body_width, body_height)
        self.title << Paragraph(self.document.metadata['title'],
                                style='title page title')
        if 'subtitle' in self.document.metadata:
            self.title << Paragraph(self.document.metadata['subtitle'],
                                    style='title page subtitle')
        if 'author' in self.document.metadata and options['show_author']:
            self.title << Paragraph(self.document.metadata['author'],
                                    style='title page author')
        if options['show_date']:
            date = self.document.metadata['date']
            try:
                self.title << Paragraph(date.strftime('%B %d, %Y'),
                                        style='title page date')
            except AttributeError:
                self.title << Paragraph(date, style='title page date')
        extra = options['extra']
        if extra:
            self.title << Paragraph(extra, style='title page extra')


# document parts
# ----------------------------------------------------------------------------

class TitlePart(DocumentPart):
    def first_page(self):
        return TitlePage(self, self.document.options['page_size'],
                         self.document.options['page_orientation'])

    def new_page(self, chains):
        assert False, 'TitlePart can consist of only one page!'


class FrontMatterPart(BookPart):
    footer = Tab() + Variable(PAGE_NUMBER)

    def __init__(self, document_section, flowables):
        self._flowables = flowables
        super().__init__(document_section)

    def flowables(self):
        return self._flowables


class FrontMatter(DocumentSection):
    page_number_format = ROMAN_LC
    parts = [TitlePart]

    def __init__(self, document):
        super().__init__(document)
        for flowables in document.front_matter:
            self._parts.append(FrontMatterPart(self, flowables))


class BodyMatter(DocumentSection):
    parts = [ContentsPart]


# main document
# ----------------------------------------------------------------------------

class BookOptions(DocumentOptions):
    extra = Option(MixedStyledText, None, 'Extra text to include on the title '
                   'page below the title')


class Book(DocumentTemplate):
    sections = [FrontMatter, BodyMatter]
    options_class = BookOptions
