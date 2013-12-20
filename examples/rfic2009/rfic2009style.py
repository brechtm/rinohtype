
from rinoh.dimension import PT, INCH, CM
from rinoh.font import TypeFace, TypeFamily
from rinoh.font.type1 import Type1Font
from rinoh.font.opentype import OpenTypeFont
from rinoh.font.style import REGULAR, MEDIUM, BOLD, ITALIC
from rinoh.paper import Paper, LETTER
from rinoh.document import Document, Page, PORTRAIT
from rinoh.layout import Container, DownExpandingContainer, Chain
from rinoh.layout import TopFloatContainer, FootnoteContainer
from rinoh.paragraph import ParagraphStyle, Paragraph, LEFT, RIGHT, CENTER, BOTH
from rinoh.paragraph import ProportionalSpacing, FixedSpacing, TabStop
from rinoh.number import CHARACTER_UC, ROMAN_UC, NUMBER
from rinoh.text import SingleStyledText, MixedStyledText
from rinoh.text import Bold, Emphasized, SmallCaps, Superscript, Subscript
from rinoh.text import TextStyle, BOLD_ITALIC_STYLE
from rinoh.text import Tab as RinohTab
from rinoh.math import MathFonts, MathStyle, Equation, EquationStyle
from rinoh.math import Math as RinohMath
from rinoh.structure import Heading, List, ListItem
from rinoh.structure import HeadingStyle, ListStyle
from rinoh.structure import Header, Footer, HeaderStyle, FooterStyle
from rinoh.structure import TableOfContents, TableOfContentsStyle
from rinoh.reference import Field, Reference, REFERENCE
from rinoh.reference import Footnote as RinohFootnote
from rinoh.flowable import Flowable, FlowableStyle, GroupedFlowables, Floating
from rinoh.float import Figure as RinohFigure, CaptionStyle
from rinoh.table import Tabular as RinohTabular, MIDDLE
from rinoh.table import HTMLTabularData, CSVTabularData, TabularStyle, CellStyle
from rinoh.draw import LineStyle, RED
from rinoh.style import PARENT_STYLE, StyleStore, ClassSelector, ContextSelector
from rinoh.frontend.xml import element_factory
from rinoh.backend import pdf

import rinoh.frontend.xml.elementtree as xml_frontend

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import Citation, CitationItem, Locator



# use Gyre Termes instead of (PDF Core) Times
use_gyre = True

# fonts
# ----------------------------------------------------------------------------
if use_gyre:
    #termes_roman = Type1Font("../fonts/qtmr", weight=REGULAR)
    termes_roman = OpenTypeFont("../fonts/texgyretermes-regular.otf",
                                weight=REGULAR)
    #termes_roman = OpenTypeFont(r"C:\Windows\Fonts\times.ttf", weight=REGULAR)
    termes_italic = Type1Font("../fonts/qtmri", weight=REGULAR, slant=ITALIC)
    termes_bold = Type1Font("../fonts/qtmb", weight=BOLD)
    termes_bold_italic = Type1Font("../fonts/qtmbi", weight=BOLD, slant=ITALIC)

    termes = TypeFace("TeXGyreTermes", termes_roman, termes_bold,
                      termes_italic, termes_bold_italic)
    cursor_regular = Type1Font("../fonts/qcrr", weight=REGULAR)
    cursor = TypeFace("TeXGyreCursor", cursor_regular)

    ieeeFamily = TypeFamily(serif=termes, mono=cursor)

    schola_roman = Type1Font("../fonts/qcsr", weight=REGULAR)
    schola_italic = Type1Font("../fonts/qcsri", weight=REGULAR, slant=ITALIC)
    schola_bold = Type1Font("../fonts/qcsb", weight=BOLD)
    heros_roman = Type1Font("../fonts/qhvr", weight=REGULAR)
    chorus = Type1Font("../fonts/qzcmi", weight=MEDIUM)
    standard_symbols = Type1Font("../fonts/usyr", weight=REGULAR)
    cmex9 = Type1Font("../fonts/cmex9", weight=REGULAR)

    mathfonts = MathFonts(schola_roman, schola_italic, schola_bold,
                          heros_roman, cursor_regular, chorus, standard_symbols,
                          cmex9)
else:
    from rinoh.fonts.adobe14 import pdf_family as ieeeFamily
    #from rinoh.fonts.adobe35 import palatino, helvetica, courier
    #from rinoh.fonts.adobe35 import newcenturyschlbk, bookman
    #ieeeFamily = TypeFamily(serif=palatino, sans=helvetica, mono=courier)
    from rinoh.fonts.adobe35 import postscript_mathfonts as mathfonts


# styles
# ----------------------------------------------------------------------------
styles = StyleStore()

styles('body', ClassSelector(Paragraph),
       typeface=ieeeFamily.serif,
       font_weight=REGULAR,
       font_size=10*PT,
       line_spacing=FixedSpacing(12*PT),
       indent_first=0.125*INCH,
       space_above=0*PT,
       space_below=0*PT,
       justify=BOTH,
       kerning=True,
       ligatures=True,
       hyphen_lang='en_US',
       hyphen_chars=4)

styles('title', ClassSelector(Paragraph, 'title'),
       typeface=ieeeFamily.serif,
       font_weight=REGULAR,
       font_size=18*PT,
       line_spacing=ProportionalSpacing(1.2),
       space_above=6*PT,
       space_below=6*PT,
       justify=CENTER)

styles('author', ClassSelector(Paragraph, 'author'),
       base='title',
       font_size=12*PT,
       line_spacing=ProportionalSpacing(1.2))

styles('affiliation', ClassSelector(Paragraph, 'affiliation'),
       base='author',
       space_below=6*PT + 12*PT)

styles('abstract', ClassSelector(Paragraph, 'abstract'),
       typeface=ieeeFamily.serif,
       font_weight=BOLD,
       font_size=9*PT,
       line_spacing=FixedSpacing(10*PT),
       indent_first=0.125*INCH,
       space_above=0*PT,
       space_below=0*PT,
       justify=BOTH)

styles('heading level 1', ClassSelector(Heading, level=1),
       typeface=ieeeFamily.serif,
       font_weight=REGULAR,
       font_size=10*PT,
       small_caps=True,
       justify=CENTER,
       line_spacing=FixedSpacing(12*PT),
       space_above=18*PT,
       space_below=6*PT,
       numbering_style=ROMAN_UC)

styles('unnumbered heading level 1', ClassSelector(Heading, 'unnumbered',
                                                   level=1),
       base='heading level 1',
       numbering_style=None)

styles('heading level 2', ClassSelector(Heading, level=2),
       base='heading level 1',
       font_slant=ITALIC,
       font_size=10*PT,
       small_caps=False,
       justify=LEFT,
       line_spacing=FixedSpacing(12*PT),
       space_above=6*PT,
       space_below=6*PT,
       numbering_style=CHARACTER_UC)

styles('list', ClassSelector(List, 'ordered'),
       base='body',
       space_above=5*PT,
       space_below=5*PT,
       indent_left=0*INCH,
       indent_first=0*INCH,
       ordered=True,
       item_spacing=0*PT,
       numbering_style=NUMBER,
       numbering_separator=')')

styles('list item paragraph', ContextSelector(ClassSelector(ListItem),
                                              ClassSelector(Paragraph)),
       base='body',
       indent_first=14*PT)

styles('header', ClassSelector(Header),
       base='body',
       indent_first=0*PT,
       font_size=9*PT)

styles('footer', ClassSelector(Footer),
       base='header',
       indent_first=0*PT,
       justify=CENTER)


# pre-load hyphenation dictionary (which otherwise occurs during page rendering,
# and thus invalidates per-page render time)
from rinoh.paragraph import HYPHENATORS
HYPHENATORS[(styles['body'].hyphen_lang, styles['body'].hyphen_chars)]

styles['math'] = MathStyle(fonts=mathfonts)

styles['equation'] = EquationStyle(base='body',
                                   math_style='math',
                                   indent_first=0*PT,
                                   space_above=6*PT,
                                   space_below=6*PT,
                                   justify=CENTER,
                                   tab_stops=[TabStop(0.5, CENTER),
                                              TabStop(1.0, RIGHT)])

styles['toc0'] = ParagraphStyle(base='body',
                                indent_first=0)
styles['toc1'] = ParagraphStyle(base='toc0',
                                font_weight=BOLD,
                                tab_stops=[TabStop(0.6*CM),
                                           TabStop(1.0, RIGHT, '. ')])
styles['toc2'] = ParagraphStyle(base='toc0',
                                indent_left=0.6*CM,
                                tab_stops=[TabStop(1.2*CM),
                                           TabStop(1.0, RIGHT, '. ')])
styles['toc3'] = ParagraphStyle(base='toc0',
                                indent_left=1.2*CM,
                                tab_stops=[TabStop(1.8*CM),
                                           TabStop(1.0, RIGHT, '. ')])

styles['toc'] = TableOfContentsStyle(base='body')

styles['bibliography'] = ParagraphStyle(base='body',
                                        font_size=9*PT,
                                        indent_first=0*PT,
                                        space_above=0*PT,
                                        space_below=0*PT,
                                        tab_stops=[TabStop(0.25*INCH, LEFT)])

styles['figure'] = FlowableStyle(space_above=10*PT,
                                 space_below=12*PT)

styles['figure caption'] = CaptionStyle(typeface=ieeeFamily.serif,
                                        font_weight=REGULAR,
                                        font_size=9*PT,
                                        line_spacing=FixedSpacing(10*PT),
                                        indent_first=0*PT,
                                        space_above=20*PT,
                                        space_below=0*PT,
                                        justify=BOTH)

styles['footnote'] = ParagraphStyle(base='body',
                                    font_size=9*PT,
                                    line_spacing=FixedSpacing(10*PT))

styles['red line'] = LineStyle(width=0.2*PT, color=RED)
styles['thick line'] = LineStyle()
styles['tabular'] = TabularStyle(typeface=ieeeFamily.serif,
                                 font_weight=REGULAR,
                                 font_size=10*PT,
                                 line_spacing=FixedSpacing(12*PT),
                                 indent_first=0*PT,
                                 space_above=0*PT,
                                 space_below=0*PT,
                                 justify=CENTER,
                                 vertical_align=MIDDLE,
                                 left_border=styles['red line'],
                                 right_border=styles['red line'],
                                 bottom_border=styles['red line'],
                                 top_border=styles['red line'])

styles['first row'] = CellStyle(font_weight=BOLD,
                                bottom_border=styles['thick line'])
styles['first column'] = CellStyle(font_slant=ITALIC,
                                   right_border=styles['thick line'])
styles['numbers'] = CellStyle(typeface=ieeeFamily.mono)
styles['tabular'].set_cell_style(styles['first row'], rows=0)
styles['tabular'].set_cell_style(styles['first column'], cols=0)
styles['tabular'].set_cell_style(styles['numbers'], rows=slice(1,None),
                                 cols=slice(1,None))

# custom paragraphs
# ----------------------------------------------------------------------------

class Abstract(Paragraph):
    def __init__(self, text):
        label = SingleStyledText("Abstract \N{EM DASH} ", BOLD_ITALIC_STYLE)
        return super().__init__(label + text, style='abstract')


class IndexTerms(Paragraph):
    def __init__(self, terms):
        label = SingleStyledText("Index Terms \N{EM DASH} ", BOLD_ITALIC_STYLE)
        text = ", ".join(sorted(terms)) + "."
        text = text.capitalize()
        return super().__init__(label + text, style='abstract')


# input parsing
# ----------------------------------------------------------------------------

CustomElement, NestedElement = element_factory(xml_frontend, styles)

class Section(CustomElement):
    def parse(self, document, level=1):
        for element in self.getchildren():
            if type(element) == Section:
                section = element.process(document, level=level + 1)
                for flowable in section:
                    yield flowable
            else:
                if isinstance(element, Title):
                    flowable = element.process(document, level=level,
                                               id=self.get('id', None))
                else:
                    flowable = element.process(document)
                yield flowable


class Title(NestedElement):
    def parse(self, document, level=1, id=None):
        return Heading(self.process_content(document), level=level, id=id)


class P(NestedElement):
    def parse(self, document):
        return Paragraph(self.process_content(document))


class B(NestedElement):
    def parse(self, document):
        return Bold(self.process_content(document))


class Em(NestedElement):
    def parse(self, document):
        return Emphasized(self.process_content(document))


class SC(NestedElement):
    def parse(self, document):
        return SmallCaps(self.process_content(document))


class Sup(NestedElement):
    def parse(self, document):
        return Superscript(self.process_content(document))


class Sub(NestedElement):
    def parse(self, document):
        return Subscript(self.process_content(document))


class Tab(CustomElement):
    def parse(self, document):
        return MixedStyledText([RinohTab()])


class OL(CustomElement):
    def parse(self, document):
        return List([li.process(document) for li in self.li], style='ordered')


class LI(CustomElement):
    def parse(self, document):
        return [item.process(document) for item in self.getchildren()]


class Math(CustomElement):
    def parse(self, document):
        return RinohMath(self.text, style='math')


class Eq(CustomElement):
    def parse(self, document, id=None):
        equation = Equation(self.text, style='equation')
        id = self.get('id', None)
        if id:
            document.elements[id] = equation
        return MixedStyledText([equation])


class Cite(CustomElement):
    def parse(self, document):
        keys = map(lambda x: x.strip(), self.get('id').split(','))
        items = [CitationItem(key) for key in keys]
        citation = Citation(items)
        document.bibliography.register(citation)
        return CitationField(citation)


class Ref(CustomElement):
    def parse(self, document):
        return Reference(self.get('id'), self.get('type', REFERENCE))


class Footnote(NestedElement):
    def parse(self, document):
        par = Paragraph(self.process_content(document),
                        style='footnote')
        return RinohFootnote(par)


class Acknowledgement(CustomElement):
    def parse(self, document):
        yield Heading('Acknowledgement', style='unnumbered', level=1)
        for element in self.getchildren():
            yield element.process(document)


class Figure(CustomElement):
    def parse(self, document):
        caption_text = self.caption.process(document)
        scale = float(self.get('scale'))
        figure = RinohFigure(self.get('path'), caption_text, scale=scale,
                             id=self.get('id', None), style='figure',
                             caption_style='figure caption')
        return Floating(figure)


class Caption(NestedElement):
    pass


class Tabular(CustomElement):
    def parse(self, document):
        data = HTMLTabularData(self)
        return RinohTabular(data, style='tabular')


class CSVTabular(CustomElement):
    def parse(self, document):
        data = CSVTabularData(self.get('path'))
        return RinohTabular(data, style='tabular')


# bibliography
# ----------------------------------------------------------------------------

from rinoh import csl_formatter


class IEEEBibliography(GroupedFlowables, list):
    def __init__(self, items):
        super().__init__()
        for item in items:
            self.append(Paragraph(item, style='bibliography'))

    def flowables(self, document):
        return iter(self)


csl_formatter.Bibliography = IEEEBibliography


class CitationField(Field):
    def __init__(self, citation):
        super().__init__()
        self.citation = citation

    def warn_unknown_reference_id(self, item, container):
        self.warn("Unknown reference ID '{}'".format(item.key), container)

    def field_spans(self, container):
        callback = lambda item: self.warn_unknown_reference_id(item, container)
        text = self.citation.bibliography.cite(self.citation, callback)
        field_text = SingleStyledText(text)
        field_text.parent = self.parent
        return field_text.spans()


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
        toc = TableOfContents(style='toc',
                              styles=[styles['toc1'], styles['toc2'],
                                      styles['toc3']])
        self.content << toc
        for section in self.root.body.section:
            for flowable in section.process(self):
                self.content << flowable
        try:
            for flowable in self.root.body.acknowledgement.process(self):
                self.content << flowable
        except AttributeError:
            pass
        self.content << Heading('References', style='unnumbered', level=1)
        self.bibliography.sort()
        self.content << self.bibliography.bibliography()

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
