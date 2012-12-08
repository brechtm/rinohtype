
from io import BytesIO

from docutils.core import publish_doctree, publish_from_doctree

import pyte.frontend
pyte.frontend.XML_FRONTEND = 'pyte.frontend.xml.elementtree'
from pyte.frontend.xml import Parser, CustomElement, NestedElement

from pyte.paragraph import Paragraph as RinohParagraph
from pyte.paragraph import ParagraphStyle, LEFT, CENTER, BOTH
from pyte.text import LiteralText, MixedStyledText, TextStyle, Emphasized, Bold
from pyte.font import TypeFace, TypeFamily
from pyte.font.style import REGULAR, BOLD, ITALIC
from pyte.font.type1 import Type1Font
from pyte.font.opentype import OpenTypeFont
from pyte.unit import pt, cm, inch
from pyte.paper import A5
from pyte.document import Document, Page, Orientation
from pyte.layout import Container, Chain, FootnoteContainer
from pyte.backend import pdf
from pyte.structure import Heading, HeadingStyle
from pyte.number import ROMAN_UC, CHARACTER_UC
from pyte.flowable import Flowable
from pyte.float import Float

pagella_regular = OpenTypeFont("../fonts/texgyrepagella-regular.otf",
                               weight=REGULAR)
pagella_italic = OpenTypeFont("../fonts/texgyrepagella-italic.otf",
                              weight=REGULAR, slant=ITALIC)
pagella_bold = OpenTypeFont("../fonts/texgyrepagella-bold.otf", weight=BOLD)
pagella_bold_italic = OpenTypeFont("../fonts/texgyrepagella-bolditalic.otf",
                                   weight=BOLD, slant=ITALIC)

pagella = TypeFace("TeXGyrePagella", pagella_regular, pagella_italic,
                   pagella_bold, pagella_bold_italic)
cursor_regular = Type1Font("../fonts/qcrr", weight=REGULAR)
cursor = TypeFace("TeXGyreCursor", cursor_regular)

fontFamily = TypeFamily(serif=pagella, mono=cursor)


titleStyle = ParagraphStyle('title',
                            typeface=fontFamily.serif,
                            font_size=16*pt,
                            line_spacing=1.2,
                            space_above=6*pt,
                            space_below=6*pt,
                            justify=CENTER)

bodyStyle = ParagraphStyle('body',
                           typeface=fontFamily.serif,
                           font_weight=REGULAR,
                           font_size=10*pt,
                           line_spacing=12*pt,
                           #indent_first=0.125*inch,
                           space_above=0*pt,
                           space_below=10*pt,
                           justify=BOTH)

literalstyle = ParagraphStyle('literal', base=bodyStyle,
                              #font_size=9*pt,
                              justify=LEFT,
                              indent_left=1*cm,
                              typeface=fontFamily.mono)
#                              noWrap=True,   # but warn on overflow
#                              literal=True ?)

blockQuotestyle = ParagraphStyle('literal', base=bodyStyle,
                                 indent_left=1*cm)

hd1Style = HeadingStyle('heading',
                        typeface=fontFamily.serif,
                        font_size=14*pt,
                        line_spacing=12*pt,
                        space_above=14*pt,
                        space_below=6*pt,
                        numbering_style=None)

hd2Style = HeadingStyle('subheading', base=hd1Style,
                        font_slant=ITALIC,
                        font_size=12*pt,
                        line_spacing=12*pt,
                        space_above=6*pt,
                        space_below=6*pt)

heading_styles = [hd1Style, hd2Style]


monoStyle = TextStyle(name="monospaced", typeface=fontFamily.mono)

class Mono(MixedStyledText):
    def __init__(self, text, y_offset=0):
        super().__init__(text, style=monoStyle, y_offset=y_offset)



class Section(CustomElement):
    def parse(self, document, level=1):
        for element in self.getchildren():
            if isinstance(element, Title):
                elem = element.parse(document, level=level,
                                     id=self.get('id', None))
            elif type(element) == Section:
                elem = element.parse(document, level=level + 1)
            else:
                elem = element.parse(document)
            if isinstance(elem, Flowable) or isinstance(elem, Float):
                yield elem
            else:
                for flw in elem:
                    yield flw


class Paragraph(NestedElement):
    def parse(self, document):
        return RinohParagraph(super().parse(document), style=bodyStyle)


class Title(CustomElement):
    def parse(self, document, level=1, id=None):
        #print('Title.render()')
        return Heading(document, self.text, style=heading_styles[level - 1],
                       level=level, id=id)

class Tip(NestedElement):
    def parse(self, document):
        return RinohParagraph('TIP: ' + super().parse(document), style=bodyStyle)


class Emphasis(CustomElement):
    def parse(self, document):
        return Emphasized(self.text)


class Strong(CustomElement):
    def parse(self, document):
        return Bold(self.text)


class Literal(CustomElement):
    def parse(self, document):
        return LiteralText(self.text, style=monoStyle)


class Literal_Block(CustomElement):
    def parse(self, document):
        return RinohParagraph(LiteralText(self.text), style=literalstyle)


class Block_Quote(NestedElement):
    def parse(self, document):
        return RinohParagraph(super().parse(document), style=blockQuotestyle)


class Reference(CustomElement):
    def parse(self, document):
        return self.text


class Footnote(CustomElement):
    def parse(self, document):
        return RinohParagraph('footnote', style=bodyStyle)


class Footnote_Reference(CustomElement):
    def parse(self, document):
        return self.text


class Target(CustomElement):
    def parse(self, document):
        return RinohParagraph('', style=bodyStyle)



class SimplePage(Page):
    topmargin = bottommargin = 2 * cm
    leftmargin = rightmargin = 2 * cm

    def __init__(self, document):
        super().__init__(document, A5, Orientation.Portrait)

        body_width = self.width - (self.leftmargin + self.rightmargin)
        body_height = self.height - (self.topmargin + self.bottommargin)
        self.body = Container(self, self.leftmargin, self.topmargin,
                              body_width, body_height)

        self.content = document.content

        self.footnote_space = FootnoteContainer(self.body, 0*pt, body_height)
        self._footnote_number = 0

        self.content = Container(self.body, 0*pt, 0*pt,
                                 bottom=self.footnote_space.top,
                                 chain=document.content)

##        self.content._footnote_space = self.footnote_space
##
##        self.header = Container(self, self.leftmargin, self.topmargin / 2,
##                                body_width, 12*pt)
##        footer_vert_pos = self.topmargin + body_height + self.bottommargin /2
##        self.footer = Container(self, self.leftmargin, footer_vert_pos,
##                                body_width, 12*pt)
##        header_text = Header(header_style)
##        self.header.add_flowable(header_text)
##        footer_text = Footer(footer_style)
##        self.footer.add_flowable(footer_text)


# main document
# ----------------------------------------------------------------------------
class ReStructuredTextDocument(Document):
    def __init__(self, filename):
        with open(filename) as file:
            doctree = publish_doctree(file.read())
        xml_buffer = BytesIO(publish_from_doctree(doctree, writer_name='xml'))
        super().__init__(xml_buffer, backend=pdf)
        self.title = self.root.title.text
        self.parse_input()

    def parse_input(self):
##        toc = TableOfContents(style=toc_style, styles=toc_levels)

        self.content_flowables = []

        self.content_flowables.append(RinohParagraph(self.title, titleStyle))

        for section in self.root.section:
##            toc.register(flowable)
            for flowable in section.parse(self):
                self.content_flowables.append(flowable)
##        try:
##            for flowable in self.root.body.acknowledgement.parse(self):
##                toc.register(flowable)
##                self.content_flowables.append(flowable)
##        except AttributeError:
##            pass

    def setup(self):
        self.page_count = 1
        self.content = Chain(self)
        page = SimplePage(self)
        self.add_page(page, self.page_count)

        for flowable in self.content_flowables:
            self.content.add_flowable(flowable)

##        bib = self.bibliography.bibliography()
##        self.content.add_flowable(bib)

    def add_to_chain(self, chain):
        page = SimplePage(self)
        self.page_count += 1
        self.add_page(page, self.page_count)
        return page.content
