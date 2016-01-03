
from rinoh.dimension import PT, CM
from rinoh.document import DocumentPart, Page
from rinoh.layout import (Container, ChainedContainer, FootnoteContainer,
                          UpExpandingContainer, DownExpandingContainer)
from rinoh.structure import Header, Footer, HorizontalRule


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


# document sections & parts
# ----------------------------------------------------------------------------

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
