# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from rinoh.dimension import PT, CM
from rinoh.document import DocumentPart, Page, DocumentSection
from rinoh.layout import (Container, ChainedContainer, FootnoteContainer,
                          UpExpandingContainer, DownExpandingContainer,
                          FlowablesContainer)
from rinoh.number import ROMAN_LC
from rinoh.paragraph import Paragraph
from rinoh.reference import Variable, PAGE_NUMBER
from rinoh.structure import Header, Footer, HorizontalRule
from rinoh.text import Tab


__all__ = ['SimplePage', 'TitlePage', 'TitlePart', 'FrontMatterPart',
           'FrontMatter', 'ContentsPart', 'BodyMatter']


# page definitions
# ----------------------------------------------------------------------------


class SimplePage(Page):
    header_footer_distance = 14*PT
    column_spacing = 1*CM

    def __init__(self, document_part, chain, title_flowables=None,
                 header=True, footer=True):
        paper = document_part.document.options['page_size']
        orientation = document_part.document.options['page_orientation']
        super().__init__(document_part, paper, orientation)
        document = document_part.document
        h_margin = document.options['page_horizontal_margin']
        v_margin = document.options['page_vertical_margin']
        num_cols = document.options['columns']
        body_width = self.width - (2 * h_margin)
        body_height = self.height - (2 * v_margin)
        total_column_spacing = self.column_spacing * (num_cols - 1)
        column_width = (body_width - total_column_spacing) / num_cols
        self.body = Container('body', self, h_margin, v_margin,
                              body_width, body_height)

        footnote_space = FootnoteContainer('footnotes', self.body, 0*PT,
                                           self.body.height)
        float_space = DownExpandingContainer('floats', self.body, 0*PT,
                                             0*PT, max_height=body_height / 2)
        self.body.float_space = float_space
        if title_flowables:
            self.title = DownExpandingContainer('title', self.body,
                                                top=float_space.bottom)
            self.title.append_flowable(title_flowables)
            column_top = self.title.bottom + self.column_spacing
        else:
            column_top = float_space.bottom
        self.columns = [ChainedContainer('column{}'.format(i + 1), self.body,
                                         chain,
                                         left=i * (column_width
                                                   + self.column_spacing),
                                         top=column_top, width=column_width,
                                         bottom=footnote_space.top)
                        for i in range(num_cols)]
        for column in self.columns:
            column._footnote_space = footnote_space

        if header and document_part.header:
            header_bottom = self.body.top - self.header_footer_distance
            self.header = UpExpandingContainer('header', self,
                                               left=h_margin,
                                               bottom=header_bottom,
                                               width=body_width)
            self.header.append_flowable(Header(document_part.header))
            self.header.append_flowable(HorizontalRule(style='header'))
        if footer and document_part.footer:
            footer_vpos = self.body.bottom + self.header_footer_distance
            self.footer = DownExpandingContainer('footer', self,
                                                 left=h_margin,
                                                 top=footer_vpos,
                                                 width=body_width)
            self.footer.append_flowable(HorizontalRule(style='footer'))
            self.footer.append_flowable(Footer(document_part.footer))


class TitlePage(Page):
    def __init__(self, document_part):
        paper = document_part.document.options['page_size']
        orientation = document_part.document.options['page_orientation']
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


# document sections & parts
# ----------------------------------------------------------------------------

class TitlePart(DocumentPart):
    page_template = TitlePage

    def flowables(self):
        return []

    def first_page(self):
        return self.page_template(self)

    def new_page(self, chains):
        assert False, 'TitlePart can consist of only one page!'


class FrontMatterPart(DocumentPart):
    page_template = SimplePage
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


class ContentsPart(DocumentPart):
    page_template = SimplePage

    @property
    def header(self):
        return self.document.options['header_text']

    @property
    def footer(self):
        return self.document.options['footer_text']

    def flowables(self):
        return self.document.content_flowables


class BodyMatter(DocumentSection):
    parts = [ContentsPart]
