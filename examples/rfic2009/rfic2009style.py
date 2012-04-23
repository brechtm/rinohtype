
from copy import copy

from lxml import etree, objectify

from pyte.unit import inch, pt, cm
from pyte.font import TypeFace, TypeFamily
from pyte.font.type1 import Type1Font
from pyte.font.style import REGULAR, BOLD, ITALIC
from pyte.paper import Paper, Letter
from pyte.document import Document, Page, Orientation
from pyte.layout import Container, DownExpandingContainer, FootnoteContainer
from pyte.layout import Chain
from pyte.paragraph import ParagraphStyle, Paragraph, LEFT, RIGHT, CENTER, BOTH
from pyte.paragraph import TabStop
from pyte.number import CHARACTER_UC, ROMAN_UC, NUMBER
from pyte.text import StyledText, MixedStyledText
from pyte.text import Bold, Emphasized, SmallCaps, Superscript, Subscript
from pyte.text import TextStyle, boldItalicStyle
from pyte.text import Tab as PyteTab, FlowableEmbedder
from pyte.math import MathFonts, MathStyle, Equation, EquationStyle
from pyte.math import Math as PyteMath
from pyte.structure import Heading, List
from pyte.structure import HeadingStyle, ListStyle
from pyte.structure import Header, Footer, HeaderStyle, FooterStyle
from pyte.structure import TableOfContents, TableOfContentsStyle
from pyte.reference import Field, Reference, REFERENCE
from pyte.reference import Footnote as PyteFootnote
from pyte.bibliography import Bibliography, BibliographyFormatter
from pyte.flowable import Flowable, FlowableStyle
from pyte.float import Figure as PyteFigure, CaptionStyle, Float
from pyte.table import Tabular as PyteTabular, MIDDLE
from pyte.table import HTMLTabularData, CSVTabularData, TabularStyle, CellStyle
from pyte.draw import LineStyle, RED
from pyte.style import ParentStyle
from pyte.backend import pdf, psg

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import Citation, CitationItem, Locator



# use Gyre Termes instead of (PDF Core) Times
use_gyre = True

# fonts
# ----------------------------------------------------------------------------
if use_gyre:
    from pyte.font.style import REGULAR, MEDIUM, BOLD, ITALIC

    termes_roman = Type1Font("fonts/qtmr", weight=REGULAR)
    termes_italic = Type1Font("fonts/qtmri", weight=REGULAR, slant=ITALIC)
    termes_bold = Type1Font("fonts/qtmb", weight=BOLD)
    termes_bold_italic = Type1Font("fonts/qtmbi", weight=BOLD, slant=ITALIC)

    termes = TypeFace("TeXGyreTermes", termes_roman, termes_bold,
                      termes_italic, termes_bold_italic)
    cursor_regular = Type1Font("fonts/qcrr", weight=REGULAR)
    cursor = TypeFace("TeXGyreCursor", cursor_regular)

    ieeeFamily = TypeFamily(serif=termes, mono=cursor)

    schola_roman = Type1Font("fonts/qcsr", weight=REGULAR)
    schola_italic = Type1Font("fonts/qcsri", weight=REGULAR, slant=ITALIC)
    schola_bold = Type1Font("fonts/qcsb", weight=BOLD)
    heros_roman = Type1Font("fonts/qhvr", weight=REGULAR)
    chorus = Type1Font("fonts/qzcmi", weight=MEDIUM)
    standard_symbols = Type1Font("fonts/usyr", weight=REGULAR)
    cmex9 = Type1Font("fonts/cmex9", weight=REGULAR)

    mathfonts = MathFonts(schola_roman, schola_italic, schola_bold,
                          heros_roman, cursor_regular, chorus, standard_symbols,
                          cmex9)
else:
    from pyte.fonts.adobe14 import pdf_family as ieeeFamily
    #from pyte.fonts.adobe35 import palatino, helvetica, courier
    #from pyte.fonts.adobe35 import newcenturyschlbk, bookman
    #ieeeFamily = TypeFamily(serif=palatino, sans=helvetica, mono=courier)
    from pyte.fonts.adobe35 import postscript_mathfonts as mathfonts


# paragraph styles
# ----------------------------------------------------------------------------
bodyStyle = ParagraphStyle('body',
                           typeface=ieeeFamily.serif,
                           fontWeight=REGULAR,
                           fontSize=10*pt,
                           lineSpacing=12*pt,
                           indentFirst=0.125*inch,
                           spaceAbove=0*pt,
                           spaceBelow=0*pt,
                           justify=BOTH)

#TextStyle.attributes['kerning'] = False
#TextStyle.attributes['ligatures'] = False

ParagraphStyle.attributes['typeface'] = bodyStyle.typeface
ParagraphStyle.attributes['hyphenLang'] = 'en_US'
ParagraphStyle.attributes['hyphenChars'] = 4

mathstyle = MathStyle('math', fonts=mathfonts)

equationstyle = EquationStyle('equation', base=bodyStyle,
                              math_style=mathstyle,
                              indentFirst=0*pt,
                              spaceAbove=6*pt,
                              spaceBelow=6*pt,
                              justify=CENTER,
                              tab_stops=[TabStop(0.5, CENTER),
                                         TabStop(1.0, RIGHT)])

toc_base_style = ParagraphStyle('toc level 1', base=bodyStyle,
                                tab_stops=[TabStop(0.6*cm),
                                           TabStop(1.0, RIGHT, '. ')])
toc_levels = [ParagraphStyle('toc level 1', fontWeight=BOLD,
                             base=toc_base_style),
              ParagraphStyle('toc level 2', indentLeft=0.5*cm,
                             base=toc_base_style),
              ParagraphStyle('toc level 3', indentLeft=1.0*cm,
                             base=toc_base_style)]
toc_style = TableOfContentsStyle('toc', base=bodyStyle)

bibliographyStyle = ParagraphStyle('bibliography', base=bodyStyle,
                                   fontSize=9*pt,
                                   indentFirst=0*pt,
                                   spaceAbove=0*pt,
                                   spaceBelow=0*pt,
                                   tab_stops=[TabStop(0.25*inch, LEFT)])

titleStyle = ParagraphStyle("title",
                            typeface=ieeeFamily.serif,
                            fontWeight=REGULAR,
                            fontSize=18*pt,
                            lineSpacing=1.2,
                            spaceAbove=6*pt,
                            spaceBelow=6*pt,
                            justify=CENTER)

authorStyle = ParagraphStyle("author",
                             base=titleStyle,
                             fontSize=12*pt,
                             lineSpacing=1.2)

affiliationStyle = ParagraphStyle("affiliation",
                                  base=authorStyle,
                                  spaceBelow=6*pt + 12*pt)

abstractStyle = ParagraphStyle("abstract",
                               typeface=ieeeFamily.serif,
                               fontWeight=BOLD,
                               fontSize=9*pt,
                               lineSpacing=10*pt,
                               indentFirst=0.125*inch,
                               spaceAbove=0*pt,
                               spaceBelow=0*pt,
                               justify=BOTH)

listStyle = ListStyle("list", base=bodyStyle,
                      spaceAbove=5*pt,
                      spaceBelow=5*pt,
                      indentLeft=0*inch,
                      indentFirst=0*inch,
                      ordered=True,
                      itemSpacing=0*pt,
                      numberingStyle=NUMBER,
                      numberingSeparator=')')

hd1Style = HeadingStyle("heading",
                        typeface=ieeeFamily.serif,
                        fontWeight=REGULAR,
                        fontSize=10*pt,
                        smallCaps=True,
                        justify=CENTER,
                        lineSpacing=12*pt,
                        spaceAbove=18*pt,
                        spaceBelow=6*pt,
                        numberingStyle=ROMAN_UC)

unnumbered_heading_style = HeadingStyle("unnumbered", base=hd1Style,
                                        numberingStyle=None)

hd2Style = HeadingStyle("subheading", base=hd1Style,
                        fontSlant=ITALIC,
                        fontSize=10*pt,
                        smallCaps=False,
                        justify=LEFT,
                        lineSpacing=12*pt,
                        spaceAbove=6*pt,
                        spaceBelow=6*pt,
                        numberingStyle=CHARACTER_UC)
#TODO: should only specify style once for each level!

heading_styles = [hd1Style, hd2Style]

header_style = HeaderStyle('header', base=bodyStyle,
                           indentFirst=0 * pt,
                           fontSize=9 * pt)

footer_style = FooterStyle('footer', base=header_style,
                           indentFirst=0 * pt,
                           justify=CENTER)

figure_style = FlowableStyle('figure',
                             spaceAbove=10 * pt,
                             spaceBelow=12 * pt)

fig_caption_style = CaptionStyle('figure caption',
                                 typeface=ieeeFamily.serif,
                                 fontWeight=REGULAR,
                                 fontSize=9*pt,
                                 lineSpacing=10*pt,
                                 indentFirst=0*pt,
                                 spaceAbove=20*pt,
                                 spaceBelow=0*pt,
                                 justify=BOTH)

footnote_style = ParagraphStyle('footnote', base=bodyStyle,
                                fontSize=9*pt,
                                lineSpacing=10*pt)

red_line_style = LineStyle('tabular line', width=0.2*pt, color=RED)
thick_line_style = LineStyle('tabular line')
tabular_style = TabularStyle('tabular',
                             typeface=ieeeFamily.serif,
                             fontWeight=REGULAR,
                             fontSize=10*pt,
                             lineSpacing=12*pt,
                             indentFirst=0*pt,
                             spaceAbove=0*pt,
                             spaceBelow=0*pt,
                             justify=CENTER,
                             vertical_align=MIDDLE,
                             left_border=red_line_style,
                             right_border=red_line_style,
                             bottom_border=red_line_style,
                             top_border=red_line_style,
                             )
first_row_style = CellStyle('first row', fontWeight=BOLD,
                            bottom_border=thick_line_style)
first_column_style = CellStyle('first column', fontSlant=ITALIC,
                               right_border=thick_line_style)
numbers_style = CellStyle('numbers', typeface=ieeeFamily.mono)
tabular_style.set_cell_style(first_row_style, rows=0)
tabular_style.set_cell_style(first_column_style, cols=0)
tabular_style.set_cell_style(numbers_style, rows=slice(1,None),
                             cols=slice(1,None))

# custom paragraphs
# ----------------------------------------------------------------------------

class Abstract(Paragraph):
    def __init__(self, text):
        label = StyledText("Abstract &mdash; ", boldItalicStyle)
        return super().__init__([label, text], abstractStyle)


class IndexTerms(Paragraph):
    def __init__(self, terms):
        label = StyledText("Index Terms &mdash; ", boldItalicStyle)
        text = ", ".join(sorted(terms)) + "."
        text = text.capitalize()
        return super().__init__([label, text], abstractStyle)


# render methods
# ----------------------------------------------------------------------------

# ElementBase restrictions!!
# http://codespeak.net/lxml/element_classes.html

# is it a good idea to inherit from ObjectifiedElement (not documented)?
class CustomElement(objectify.ObjectifiedElement):
#class CustomElement(etree.ElementBase):
    def parse(self, document):
        raise NotImplementedError('tag: %s' % self.tag)


class Section(CustomElement):
    def parse(self, document, level=1):
        #print('Section.render() %s' % self.attrib['title'])
        for element in self.getchildren():
            if isinstance(element, Title):
                elem = element.parse(document, level=level, id=self.get('id', None))
            elif type(element) == Section:
                elem = element.parse(document, level=level + 1)
            else:
                elem = element.parse(document)
            if isinstance(elem, Flowable):
                yield elem
            elif isinstance(elem, Float):
                yield elem
            else:
                for flw in elem:
                    yield flw


class Title(CustomElement):
    def parse(self, document, level=1, id=None):
        #print('Title.render()')
        return Heading(document, self.text, style=heading_styles[level - 1],
                          level=level, id=id)


class P(CustomElement):
    def parse(self, document):
        #print('P.render()')
        if self.text is not None:
            content = self.text
        else:
            content = ''
        for child in self.getchildren():
            content += child.parse(document)
            if child.tail is not None:
                content += child.tail
        return Paragraph(content, style=bodyStyle)


class B(CustomElement):
    def parse(self, document):
        #print('B.render()')
        return Bold(self.text)


class Em(CustomElement):
    def parse(self, document):
        #print('Em.render()')
        return Emphasized(self.text)


class SC(CustomElement):
    def parse(self, document):
        #print('SC.render()')
        return SmallCaps(self.text)


class Sup(CustomElement):
    def parse(self, document):
        return Superscript(self.text)


class Sub(CustomElement):
    def parse(self, document):
        return Subscript(self.text)


class Tab(CustomElement):
    def parse(self, document):
        return MixedStyledText([PyteTab()])


class OL(CustomElement):
    def parse(self, document):
        #print('OL.render()')
        items = []
        for item in self.getchildren():
            items.append(item.parse(document))
        return List(items, style=listStyle)


class LI(CustomElement):
    def parse(self, document):
        #print('LI.render()')
        content = self.text
        for child in self.getchildren():
            content += child.parse(document)
            if child.tail is not None:
                content += child.tail
        return content


class Math(CustomElement):
    def parse(self, document):
        math = PyteMath(self.text, style=mathstyle)
        return math


class Eq(CustomElement):
    def parse(self, document, id=None):
        equation = Equation(self.text, style=equationstyle)
        id = self.get('id', None)
        if id:
            document.elements[id] = equation
        return MixedStyledText([FlowableEmbedder(equation)])


class Cite(CustomElement):
    def parse(self, document):
        #print('Cite.render()')
        keys = map(lambda x: x.strip(), self.get('id').split(','))
        items = [CitationItem(key) for key in keys]
        citation = Citation(items)
        document.bibliography.register(citation)
        return CitationField(citation)


class Ref(CustomElement):
    def parse(self, document):
        #print('Ref.render()')
        return Reference(self.get('id'), self.get('type', REFERENCE))


class Footnote(CustomElement):
    def parse(self, document):
        if self.text is not None:
            content = self.text
        else:
            content = ''
        for child in self.getchildren():
            content += child.parse(document)
            if child.tail is not None:
                content += child.tail
        content = Paragraph(content, style=footnote_style)
        return PyteFootnote(content)


class Acknowledgement(CustomElement):
    def parse(self, document):
        #print('Acknowledgement.render()')
        yield Heading(document, 'Acknowledgement',
                      style=unnumbered_heading_style, level=1)
        for element in self.getchildren():
            yield element.parse(document)


class Figure(CustomElement):
    def parse(self, document):
        #print('Figure.render()')
        caption_text = self.getchildren()[0].text
        scale = float(self.get('scale'))
        figure = PyteFigure(document, self.get('path'), caption_text,
                            scale=scale, style=figure_style,
                            caption_style=fig_caption_style)
        return Float(figure)


class Tabular(CustomElement):
    def parse(self, document):
        #print('Tabular.render()')
        data = HTMLTabularData(self)
        return PyteTabular(data, style=tabular_style)


class CSVTabular(CustomElement):
    def parse(self, document):
        #print('Tabular.render()')
        data = CSVTabularData(self.get('path'))
        return PyteTabular(data, style=tabular_style)


# bibliography
# ----------------------------------------------------------------------------

from pyte import csl_formatter

class IEEEBibliography(Paragraph):
    def __init__(self, items):
        items = [FlowableEmbedder(Paragraph(item, style=ParentStyle))
                 for item in items]
        for item in items:
            item.parent = self
        return super().__init__(items, style=bibliographyStyle)

csl_formatter.Bibliography = IEEEBibliography


class CitationField(Field):
    def __init__(self, citation):
        super().__init__()
        self.citation = citation

    def field_spans(self):
        try:
            text = self.citation.bibliography.cite(self.citation)
        except AttributeError:
            text = '[?]'
        field_text = StyledText(text)
        field_text.parent = self.parent
        return field_text.spans()


# pages and their layout
# ----------------------------------------------------------------------------

class RFICPage(Page):
    topmargin = bottommargin = 1.125 * inch
    leftmargin = rightmargin = 0.85 * inch
    column_spacing = 0.25 * inch

    def __init__(self, document, first=False):
        super().__init__(document, Letter, Orientation.Portrait)

        body_width = self.width - (self.leftmargin + self.rightmargin)
        body_height = self.height - (self.topmargin + self.bottommargin)
        body = Container(self, self.leftmargin, self.topmargin,
                         body_width, body_height)

        column_width = (body.width - self.column_spacing) / 2.0
        column_top = 0 * pt
        if first:
            self.title_box = DownExpandingContainer(body)
            column_top = self.title_box.bottom

        self.float_space = DownExpandingContainer(body, top=column_top)
        column_top = self.float_space.bottom

        self.content = document.content

        self.footnote_space = FootnoteContainer(body, 0*pt, body_height)
        self._footnote_number = 0

        self.column1 = Container(body, 0*pt, column_top,
                                 width=column_width,
                                 bottom=self.footnote_space.top,
                                 chain=document.content)
        self.column2 = Container(body, column_width + self.column_spacing, column_top,
                                 width=column_width,
                                 bottom=self.footnote_space.top,
                                 chain=document.content)

        self.column1._footnote_space = self.footnote_space
        self.column2._footnote_space = self.footnote_space
        self.column1._float_space = self.float_space
        self.column2._float_space = self.float_space

        self.header = Container(self, self.leftmargin, self.topmargin / 2,
                                body_width, 12*pt)
        footer_vert_pos = self.topmargin + body_height + self.bottommargin /2
        self.footer = Container(self, self.leftmargin, footer_vert_pos,
                                body_width, 12*pt)
        header_text = Header(header_style)
        self.header.add_flowable(header_text)
        footer_text = Footer(footer_style)
        self.footer.add_flowable(footer_text)


# main document
# ----------------------------------------------------------------------------
class RFIC2009Paper(Document):
    rngschema = 'rfic.rng'

    def __init__(self, filename, bibliography_source):
        lookup = etree.ElementNamespaceClassLookup()
        namespace = lookup.get_namespace('http://www.mos6581.org/ns/rficpaper')
        namespace[None] = CustomElement
        namespace.update(dict([(cls.__name__.lower(), cls)
                               for cls in CustomElement.__subclasses__()]))

        Document.__init__(self, filename, self.rngschema, lookup, backend=pdf)

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
        self.bibliography.sort()

    def parse_input(self):
        self.title_par = Paragraph(self.title, titleStyle)
        self.author_par = Paragraph(self.author, authorStyle)
        self.affiliation_par = Paragraph(self.root.head.affiliation.text,
                                         affiliationStyle)
        toc = TableOfContents(style=toc_style, styles=toc_levels)

        self.content_flowables = [Abstract(self.root.head.abstract.text),
                                  IndexTerms(self.keywords),
                                  Heading(self, 'Table of Contents',
                                          style=unnumbered_heading_style,
                                          level=1),
                                  toc]

        for section in self.root.body.section:
            for flowable in section.parse(self):
                toc.register(flowable)
                self.content_flowables.append(flowable)
        try:
            for flowable in self.root.body.acknowledgement.parse(self):
                toc.register(flowable)
                self.content_flowables.append(flowable)
        except AttributeError:
            pass
        bib_heading = Heading(self, 'References',
                              style=unnumbered_heading_style, level=1)
        self.content_flowables.append(bib_heading)

    def setup(self):
        self.page_count = 1
        self.content = Chain(self)
        page = RFICPage(self, first=True)
        self.add_page(page, self.page_count)

        page.title_box.add_flowable(self.title_par)
        page.title_box.add_flowable(self.author_par)
        page.title_box.add_flowable(self.affiliation_par)

        for flowable in self.content_flowables:
            self.content.add_flowable(flowable)

        bib = self.bibliography.bibliography()
        self.content.add_flowable(bib)

    def add_to_chain(self, chain):
        page = RFICPage(self)
        self.page_count += 1
        self.add_page(page, self.page_count)
        return page.column1
