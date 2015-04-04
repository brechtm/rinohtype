
from rinoh.document import Document, DocumentPart, Page, PORTRAIT
from rinoh.dimension import PT, CM
from rinoh.layout import (Container, FootnoteContainer, Chain,
                          UpExpandingContainer, DownExpandingContainer)
from rinoh.paper import A4

from rinoh.structure import Section, Heading, TableOfContents, Header, Footer
from rinoh.util import NotImplementedAttribute

from ..stylesheets.somestyle import stylesheet as STYLESHEET


# page definitions
# ----------------------------------------------------------------------------

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


# document sections & parts
# ----------------------------------------------------------------------------

class BookPart(DocumentPart):
    def __init__(self, document_section):
        super().__init__(document_section)
        self.chain = Chain(self)

    def first_page(self):
        return self.new_page([self.chain])

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


class DocumentOptions(dict):
    options = {'stylesheet': STYLESHEET,
               'page_size': A4,
               'page_orientation': PORTRAIT,
               'page_horizontal_margin': 2*CM,
               'page_vertical_margin': 3*CM,
               'header_text': None,
               'footer_text': None}

    def __init__(self, **options):
        for name, value in options.items():
            self._get_default(name)
            self[name] = value

    def _get_default(self, name):
        for cls in type(self).__mro__:
            try:
                return cls.options[name]
            except KeyError:
                continue
            except AttributeError:
                raise ValueError("Unknown option '{}'".format(name))

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self._get_default(key)


class DocumentBase(Document):
    sections = NotImplementedAttribute()
    options_class = DocumentOptions

    def __init__(self, content_tree, options=None, backend=None):
        self.options = options or self.options_class()
        super().__init__(content_tree, self.options['stylesheet'],
                         backend=backend)
