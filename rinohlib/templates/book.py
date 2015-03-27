
from rinoh.document import (Document, DocumentPart, Page, DocumentSection,
                            PORTRAIT)
from rinoh.dimension import PT, CM
from rinoh.layout import (Container, FootnoteContainer, Chain,
                          UpExpandingContainer, DownExpandingContainer)
from rinoh.paragraph import Paragraph
from rinoh.paper import A4

from rinoh.structure import Section, Heading, TableOfContents, Header, Footer

from rinohlib.stylesheets.somestyle import stylesheet as STYLESHEET


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


class SimplePage(Page):
    header_footer_distance = 14*PT

    def __init__(self, chain, paper, orientation, header_footer=True):
        super().__init__(chain.document_part, paper, orientation)
        h_margin = self.document.options['page_horizontal_margin']
        v_margin = self.document.options['page_vertical_margin']
        body_width = self.width - (2 * h_margin)
        body_height = self.height - (2 * v_margin)
        self.body = Container('body', self, h_margin, v_margin,
                              body_width, body_height)

        self.footnote_space = FootnoteContainer('footnotes', self.body, 0*PT,
                                                body_height)
        self.content = Container('content', self.body, 0*PT, 0*PT,
                                 bottom=self.footnote_space.top,
                                 chain=chain)

        self.content._footnote_space = self.footnote_space

        if header_footer:
            header_bottom = self.body.top - self.header_footer_distance
            self.header = UpExpandingContainer('header', self,
                                               left=h_margin,
                                               bottom=header_bottom,
                                               width=body_width)
            footer_vpos = self.body.bottom + self.header_footer_distance
            self.footer = DownExpandingContainer('footer', self,
                                                 left=h_margin,
                                                 top=footer_vpos,
                                                 width=body_width)
            header_text = self.document.options['header_text']
            footer_text = self.document.options['footer_text']
            self.header.append_flowable(Header(header_text))
            self.footer.append_flowable(Footer(footer_text))


# document parts
# ----------------------------------------------------------------------------

class TitlePart(DocumentPart):
    def init(self):
        self.add_page(self.new_page(None))

    def new_page(self, chains):
        assert chains is None
        return TitlePage(self, self.document.options['page_size'],
                         self.document.options['page_orientation'])


class BookPart(DocumentPart):
    def __init__(self, document_section):
        super().__init__(document_section)
        self.chain = Chain(self)

    def init(self):
        self.add_page(self.new_page([self.chain]))

    def new_page(self, chains):
        chain, = chains
        return SimplePage(chain, self.document.options['page_size'],
                          self.document.options['page_orientation'],
                          header_footer=self.header_footer)


class TableOfContentsPart(BookPart):
    header_footer = True

    def __init__(self, document_section):
        super().__init__(document_section)
        self.chain << Section([Heading('Table of Contents', style='unnumbered'),
                               TableOfContents()],
                              style='table of contents')


class ContentsPart(BookPart):
    header_footer = True

    def __init__(self, document_section):
        super().__init__(document_section)
        for child in self.document.content_tree.getchildren():
            self.chain << child.flowable()


class FrontMatter(DocumentSection):
    parts = [TitlePart, TableOfContentsPart]


class BodyMatter(DocumentSection):
    parts = [ContentsPart]


# main document
# ----------------------------------------------------------------------------
class Book(Document):
    sections = [FrontMatter, BodyMatter]

    def __init__(self, content_tree, options=None, backend=None):
        super().__init__(content_tree, options['stylesheet'], backend=backend)
        self.options = options or BookOptions()


class BookOptions(dict):
    options = {'extra': None,
               'stylesheet': STYLESHEET,
               'page_size': A4,
               'page_orientation': PORTRAIT,
               'page_horizontal_margin': 2*CM,
               'page_vertical_margin': 3*CM,
               'header_text': None,
               'footer_text': None}

    def __init__(self, **options):
        for name, value in options.items():
            if name not in self.options:
                raise ValueError("Unknown option '{}'".format(name))
            self[name] = value

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.options[key]
