
from rinoh.dimension import PT, INCH
from rinoh.font.style import BOLD
from rinoh.paper import LETTER
from rinoh.document import Document, Page, PORTRAIT
from rinoh.layout import Container, DownExpandingContainer, Chain
from rinoh.layout import TopFloatContainer, FootnoteContainer
from rinoh.paragraph import Paragraph, LEFT, BOTH
from rinoh.paragraph import FixedSpacing, TabStop
from rinoh.text import SingleStyledText, MixedStyledText
from rinoh.text import Bold, Emphasized, SmallCaps, Superscript, Subscript
from rinoh.text import BOLD_ITALIC_STYLE
from rinoh.text import Tab as RinohTab
from rinoh.structure import Heading, List, Header, Footer
from rinoh.structure import TableOfContents
from rinoh.reference import Field, Reference, REFERENCE, FootnoteParagraph
from rinoh.reference import Footnote as RinohFootnote
from rinoh.flowable import GroupedFlowables, Float
from rinoh.float import Figure as RinohFigure
from rinoh.table import Tabular as RinohTabular
from rinoh.table import HTMLTabularData, CSVTabularData
from rinoh.style import ClassSelector, ContextSelector
from rinoh.frontend.xml import element_factory
from rinoh.backend import pdf

import rinoh.frontend.xml.elementtree as xml_frontend

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import Citation, CitationItem
from rinoh import csl_formatter

from rinohlib.stylesheets.ieee import styles

# pre-load hyphenation dictionary (which otherwise occurs during page rendering,
# and thus invalidates per-page render time)
from rinoh.paragraph import HYPHENATORS
HYPHENATORS[(styles['body'].hyphen_lang, styles['body'].hyphen_chars)]

# styles['math'] = MathStyle(fonts=mathfonts)
#
# styles['equation'] = EquationStyle(base='body',
#                                    math_style='math',
#                                    indent_first=0*PT,
#                                    space_above=6*PT,
#                                    space_below=6*PT,
#                                    justify=CENTER,
#                                    tab_stops=[TabStop(0.5, CENTER),
#                                               TabStop(1.0, RIGHT)])

# custom paragraphs
# ----------------------------------------------------------------------------

class Abstract(Paragraph):
    def __init__(self, text):
        label = SingleStyledText("Abstract \N{EM DASH} ", BOLD_ITALIC_STYLE)
        return super().__init__(label + text)


class IndexTerms(Paragraph):
    def __init__(self, terms):
        label = SingleStyledText("Index Terms \N{EM DASH} ", BOLD_ITALIC_STYLE)
        text = ", ".join(sorted(terms)) + "."
        text = text.capitalize()
        return super().__init__(label + text)


styles('abstract', ClassSelector(Abstract),
       base='body',
       font_weight=BOLD,
       font_size=9*PT,
       line_spacing=FixedSpacing(10*PT),
       indent_first=0.125*INCH,
       space_above=0*PT,
       space_below=0*PT,
       justify=BOTH)

styles('index terms', ClassSelector(IndexTerms),
       base='abstract')


# input parsing
# ----------------------------------------------------------------------------

CustomElement, NestedElement = element_factory(xml_frontend)

class Section(CustomElement):
    def parse(self, level=1):
        for element in self.getchildren():
            if type(element) == Section:
                section = element.process(level=level + 1)
                for flowable in section:
                    yield flowable
            else:
                if isinstance(element, Title):
                    flowable = element.process(level=level,
                                               id=self.get('id', None))
                else:
                    flowable = element.process()
                yield flowable


class Title(NestedElement):
    def parse(self, level=1, id=None):
        return Heading(self.process_content(), level=level, id=id)


class P(NestedElement):
    def parse(self):
        return Paragraph(self.process_content())


class B(NestedElement):
    def parse(self):
        return Bold(self.process_content())


class Em(NestedElement):
    def parse(self):
        return Emphasized(self.process_content())


class SC(NestedElement):
    def parse(self):
        return SmallCaps(self.process_content())


class Sup(NestedElement):
    def parse(self):
        return Superscript(self.process_content())


class Sub(NestedElement):
    def parse(self):
        return Subscript(self.process_content())


class Tab(CustomElement):
    def parse(self):
        return MixedStyledText([RinohTab()])


class OL(CustomElement):
    def parse(self):
        return List([li.process() for li in self.li], style='ordered')


class LI(CustomElement):
    def parse(self):
        return [item.process() for item in self.getchildren()]


# class Math(CustomElement):
#     def parse(self):
#         return RinohMath(self.text, style='math')
#
#
# class Eq(CustomElement):
#     def parse(self, id=None):
#         equation = Equation(self.text, style='equation')
#         id = self.get('id', None)
#         if id:
#             document.elements[id] = equation
#         return MixedStyledText([equation])


class Cite(CustomElement):
    def parse(self):
        keys = map(lambda x: x.strip(), self.get('id').split(','))
        items = [CitationItem(key) for key in keys]
        citation = Citation(items)
        return CitationField(citation)


class Ref(CustomElement):
    def parse(self):
        return Reference(self.get('id'), self.get('type', REFERENCE))


class Footnote(NestedElement):
    def parse(self):
        par = FootnoteParagraph(self.process_content())
        return RinohFootnote(par)


class Acknowledgement(CustomElement):
    def parse(self):
        yield Heading('Acknowledgement', style='unnumbered', level=1)
        for element in self.getchildren():
            yield element.process()


class Figure(CustomElement):
    def parse(self):
        caption_text = self.caption.process()
        scale = float(self.get('scale'))
        figure = RinohFigure(self.get('path'), caption_text, scale=scale,
                             id=self.get('id', None))
        return Float(figure)


class Caption(NestedElement):
    pass


class Tabular(CustomElement):
    def parse(self):
        data = HTMLTabularData(self)
        return RinohTabular(data)


class CSVTabular(CustomElement):
    def parse(self):
        data = CSVTabularData(self.get('path'))
        return RinohTabular(data)


# bibliography
# ----------------------------------------------------------------------------

class CitationField(Field):
    def __init__(self, citation):
        super().__init__()
        self.citation = citation

    def prepare(self, document):
        document.bibliography.register(self.citation)

    def warn_unknown_reference_id(self, item, container):
        self.warn("Unknown reference ID '{}'".format(item.key), container)

    def field_spans(self, container):
        callback = lambda item: self.warn_unknown_reference_id(item, container)
        text = self.citation.bibliography.cite(self.citation, callback)
        field_text = SingleStyledText(text)
        field_text.parent = self.parent
        return field_text.spans()


class Bibliography(GroupedFlowables):
    location = 'bibliography'

    def __init__(self, bibliography, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.source = self
        self.bibliography = bibliography

    def flowables(self, document):
        for entry in self.bibliography.bibliography():
            yield Paragraph(entry, parent=self)


styles('bibliography entry', ContextSelector(ClassSelector(Bibliography),
                                             ClassSelector(Paragraph)),
       base='body',  # TODO: if no base, fall back to next-best selector match?
       font_size=9*PT,
       indent_first=0*PT,
       space_above=0*PT,
       space_below=0*PT,
       tab_stops=[TabStop(0.25*INCH, LEFT)])


# pages and their layout
# ----------------------------------------------------------------------------

class RFICPage(Page):
    topmargin = bottommargin = 1.125*INCH
    leftmargin = rightmargin = 0.85*INCH
    column_spacing = 0.25*INCH

    def __init__(self, document, first=False):
        super().__init__(document, LETTER, PORTRAIT)

        body_width = self.width - (self.leftmargin + self.rightmargin)
        body_height = self.height - (self.topmargin + self.bottommargin)
        body = Container('body', self, self.leftmargin, self.topmargin,
                         body_width, body_height)

        column_width = (body.width - self.column_spacing) / 2.0
        column_top = 0*PT
        if first:
            self.title_box = DownExpandingContainer('title', body)
            column_top = self.title_box.bottom

        self.float_space = TopFloatContainer('top floats', body, top=column_top)
        column_top = self.float_space.bottom

        self.content = document.content

        self.footnote_space = FootnoteContainer('footnotes', body, 0*PT,
                                                body_height)
        self._footnote_number = 0

        self.column1 = Container('column1', body, 0*PT, column_top,
                                 width=column_width,
                                 bottom=self.footnote_space.top,
                                 chain=document.content)
        self.column2 = Container('column2', body,
                                 column_width + self.column_spacing,
                                 column_top,
                                 width=column_width,
                                 bottom=self.footnote_space.top,
                                 chain=document.content)

        self.column1._footnote_space = self.footnote_space
        self.column2._footnote_space = self.footnote_space
        self.column1.float_space = self.float_space
        self.column2.float_space = self.float_space

        self.header = Container('header', self, self.leftmargin,
                                self.topmargin / 2, body_width, 12*PT)
        footer_vert_pos = self.topmargin + body_height + self.bottommargin /2
        self.footer = Container('footer', self, self.leftmargin,
                                footer_vert_pos, body_width, 12*PT)
        header_text = Header()
        self.header.append_flowable(header_text)
        footer_text = Footer()
        self.footer.append_flowable(footer_text)


# main document
# ----------------------------------------------------------------------------
class RFIC2009Paper(Document):
    rngschema = 'rfic.rng'
    namespace = 'http://www.mos6581.org/ns/rficpaper'

    def __init__(self, filename, bibliography_source):
        super().__init__(backend=pdf)
        self.styles = styles
        parser = xml_frontend.Parser(CustomElement, self.namespace,
                                     schema=self.rngschema)
        xml_tree = parser.parse(filename)
        self.root = xml_tree.getroot()
        bibliography_style = CitationStylesStyle('ieee.csl')
        self.bibliography = CitationStylesBibliography(bibliography_style,
                                                       bibliography_source,
                                                       csl_formatter)

        authors = [author.text for author in self.root.head.authors.author]
        if len(authors) > 1:
            self.author = ', '.join(authors[:-1]) + ', and ' + authors[-1]
        else:
            self.author = authors[0]
        self.title = self.root.head.title.text
        self.keywords = [term.text for term in self.root.head.indexterms.term]
        self.parse_input()

    def parse_input(self):
        self.title_par = Paragraph(self.title, style='title')
        self.author_par = Paragraph(self.author, style='author')
        self.affiliation_par = Paragraph(self.root.head.affiliation.text,
                                         style='affiliation')

        self.content = Chain(self)
        self.content << Abstract(self.root.head.abstract.text)
        self.content << IndexTerms(self.keywords)

        self.content << Heading('Table of Contents', style='unnumbered',
                                level=1)
        toc = TableOfContents()
        self.content << toc
        for section in self.root.body.section:
            for flowable in section.process():
                self.content << flowable
        try:
            for flowable in self.root.body.acknowledgement.process():
                self.content << flowable
        except AttributeError:
            pass
        self.content << Heading('References', style='unnumbered', level=1)
        self.bibliography.sort()
        self.content << Bibliography(self.bibliography)

    def setup(self):
        self.page_count = 1
        page = RFICPage(self, first=True)
        self.add_page(page, self.page_count)

        page.title_box << self.title_par
        page.title_box << self.author_par
        page.title_box << self.affiliation_par

    def new_page(self, chains):
        page = RFICPage(self)
        self.page_count += 1
        self.add_page(page, self.page_count)
