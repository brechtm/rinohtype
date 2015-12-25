
from rinoh.dimension import DimensionBase, PT, CM
from rinoh.document import (Document, DocumentPart, Page, PageOrientation,
                            PORTRAIT)
from rinoh.layout import (Container, ChainedContainer, FootnoteContainer, Chain,
                          UpExpandingContainer, DownExpandingContainer)
from rinoh.paper import Paper, A4
from rinoh.reference import (Variable, PAGE_NUMBER, SECTION_NUMBER,
                             SECTION_TITLE, NUMBER_OF_PAGES)
from rinoh.structure import (Section, Heading, TableOfContents, Header, Footer,
                             HorizontalRule)
from rinoh.style import StyleSheet
from rinoh.text import Tab, MixedStyledText
from rinoh.util import (NotImplementedAttribute, NamedDescriptor,
                        WithNamedDescriptors)

from ..stylesheets import sphinx


# page definitions
# ----------------------------------------------------------------------------

class SimplePage(Page):
    header_footer_distance = 14*PT
    column_spacing = 1*CM

    def __init__(self, document_part, chain, paper, orientation,
                 title_flowables=None, header=True, footer=True):
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

class BookPart(DocumentPart):
    header = None
    footer = None

    def __init__(self, document_section):
        super().__init__(document_section)
        self.chain = Chain(self)
        for flowable in self.flowables():
            self.chain << flowable

    def flowables(self):
        raise NotImplementedError

    def first_page(self):
        return self.new_page([self.chain])

    def new_page(self, chains, **kwargs):
        chain, = chains
        return SimplePage(self, chain, self.document.options['page_size'],
                          self.document.options['page_orientation'], **kwargs)


class TableOfContentsSection(Section):
    def __init__(self):
        super().__init__([Heading('Table of Contents', style='unnumbered'),
                          TableOfContents()],
                         style='table of contents')

    def prepare(self, document):
        self.id = document.metadata.get('toc_id')
        super().prepare(document)


class ContentsPart(BookPart):
    @property
    def header(self):
        return self.document.options['header_text']

    @property
    def footer(self):
        return self.document.options['footer_text']

    def flowables(self):
        return self.document.content_flowables


class Option(NamedDescriptor):
    """Descriptor used to describe a document option"""
    def __init__(self, accepted_type, default_value, description):
        self.accepted_type = accepted_type
        self.default_value = default_value
        self.description = description

    def __get__(self, document_options, type=None):
        try:
            return document_options.get(self.name, self.default_value)
        except AttributeError:
            return self

    def __set__(self, document_options, value):
        if not isinstance(value, self.accepted_type):
            raise TypeError('The {} document option only accepts {} instances'
                            .format(self.name, self.accepted_type))
        document_options[self.name] = value

    @property
    def __doc__(self):
        return (':description: {} (:class:`{}`)\n'
                ':default: {}'
                .format(self.description, self.accepted_type.__name__,
                        self.default_value))


class PageOrientationPORTRAIT(object):
    pass


class DocumentOptions(dict, metaclass=WithNamedDescriptors):
    """Collects options to customize a :class:`DocumentTemplate`. Options are
    specified as keyword arguments (`options`) matching the class's
    attributes."""

    stylesheet = Option(StyleSheet, sphinx.stylesheet,
                        'The stylesheet to use for styling document elements')
    page_size = Option(Paper, A4, 'The format of the pages in the document')
    page_orientation = Option(PageOrientation, PORTRAIT,
                              'The orientation of pages in the document')
    page_horizontal_margin = Option(DimensionBase, 3*CM, 'The margin size on '
                                    'the left and the right of the page')
    page_vertical_margin = Option(DimensionBase, 3*CM, 'The margin size on the '
                                  'top and bottom of the page')
    columns = Option(int, 1, 'The number of columns for the body text')
    show_date = Option(bool, True, "Show or hide the document's date")
    show_author = Option(bool, True, "Show or hide the document's author")
    header_text = Option(MixedStyledText, Variable(SECTION_NUMBER(1))
                                          + ' ' + Variable(SECTION_TITLE(1)),
                         'The text to place in the page header')
    footer_text = Option(MixedStyledText, Tab() + Variable(PAGE_NUMBER)
                                          + '/' + Variable(NUMBER_OF_PAGES),
                         'The text to place in the page footer')

    def __init__(self, **options):
        for name, value in options.items():
            option_descriptor = getattr(type(self), name, None)
            if not isinstance(option_descriptor, Option):
                raise AttributeError('No such document option: {}'.format(name))
            setattr(self, name, value)

    def __getitem__(self, name):
        return getattr(self, name)


class DocumentTemplate(Document):
    sections = NotImplementedAttribute()
    options_class = DocumentOptions

    def __init__(self, content_flowables, options=None, backend=None):
        self.options = options or self.options_class()
        super().__init__(content_flowables, self.options['stylesheet'],
                         backend=backend)
