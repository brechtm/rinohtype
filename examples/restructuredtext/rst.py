
import rinoh as rt

from rinoh.font import TypeFace, TypeFamily
from rinoh.font.style import REGULAR, BOLD, ITALIC
from rinoh.font.type1 import Type1Font
from rinoh.font.opentype import OpenTypeFont
from rinoh.dimension import PT, CM, INCH
from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextParser


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


styles = rt.StyleStore()

styles('body', rt.ClassSelector(rt.Paragraph),
       typeface=fontFamily.serif,
       font_weight=REGULAR,
       font_size=10*PT,
       line_spacing=rt.DEFAULT,
       #indent_first=0.125*INCH,
       space_above=0*PT,
       space_below=10*PT,
       justify=rt.BOTH)

styles('title', rt.ClassSelector(rt.Paragraph, 'title'),
       typeface=fontFamily.serif,
       font_size=16*PT,
       line_spacing=rt.DEFAULT,
       space_above=6*PT,
       space_below=6*PT,
       justify=rt.CENTER)

styles('literal', rt.ClassSelector(rt.Paragraph, 'literal'),
       base='body',
       #font_size=9*PT,
       justify=rt.LEFT,
       indent_left=1*CM,
       typeface=fontFamily.mono)
       #noWrap=True,   # but warn on overflow
       #literal=True ?)

styles('block quote', rt.ClassSelector(rt.Paragraph, 'block quote'),
       base='body',
       indent_left=1*CM)

styles('heading level 1', rt.ClassSelector(rt.Heading, level=1),
       typeface=fontFamily.serif,
       font_size=14*PT,
       line_spacing=rt.DEFAULT,
       space_above=14*PT,
       space_below=6*PT,
       numbering_style=None)

styles('heading level 2', rt.ClassSelector(rt.Heading, level=2),
       base='heading level 1',
       font_slant=ITALIC,
       font_size=12*PT,
       line_spacing=rt.DEFAULT,
       space_above=6*PT,
       space_below=6*PT)

styles('monospaced', rt.ClassSelector(rt.StyledText, 'monospaced'),
       typeface=fontFamily.mono)

styles('enumerated list', rt.ClassSelector(rt.List, 'enumerated'),
       base='body',
       ordered=True,
       indent_left=5*PT,
       item_indent=12*PT,
       flowable_spacing=0*PT,
       numbering_style=rt.NUMBER,
       numbering_separator='.')

styles('bulleted list', rt.ClassSelector(rt.List, 'bulleted'),
       base='body',
       indent_left=5*PT,
       ordered=False,
       flowable_spacing=0*PT)

styles('list item paragraph', rt.ContextSelector(rt.ClassSelector(rt.ListItem),
                                                 rt.ClassSelector(rt.Paragraph)),
       base='body',
       indent_first=17*PT)

styles('definition list', rt.ClassSelector(rt.DefinitionList),
       base='body')


# page definition
# ----------------------------------------------------------------------------

class SimplePage(rt.Page):
    topmargin = bottommargin = 2*CM
    leftmargin = rightmargin = 2*CM

    def __init__(self, document):
        super().__init__(document, rt.A5, rt.PORTRAIT)

        body_width = self.width - (self.leftmargin + self.rightmargin)
        body_height = self.height - (self.topmargin + self.bottommargin)
        self.body = rt.Container('body', self, self.leftmargin, self.topmargin,
                                 body_width, body_height)

        self.content = document.content

        self.footnote_space = rt.FootnoteContainer('footnotes', self.body, 0*PT,
                                                   body_height)
        self._footnote_number = 0

        self.content = rt.Container('content', self.body, 0*PT, 0*PT,
                                    bottom=self.footnote_space.top,
                                    chain=document.content)

##        self.content._footnote_space = self.footnote_space
##
##        self.header = rt.Container(self, self.leftmargin, self.topmargin / 2,
##                                   body_width, 12*PT)
##        footer_vert_pos = self.topmargin + body_height + self.bottommargin /2
##        self.footer = rt.Container(self, self.leftmargin, footer_vert_pos,
##                                   body_width, 12*PT)
##        header_text = Header(header_style)
##        self.header.append_flowable(header_text)
##        footer_text = Footer(footer_style)
##        self.footer.append_flowable(footer_text)


# main document
# ----------------------------------------------------------------------------
class ReStructuredTextDocument(rt.Document):
    def __init__(self, filename):
        super().__init__(backend=pdf)
        self.styles = styles
        parser = ReStructuredTextParser()
        self.root = parser.parse(filename)
        self.parse_input()

    def parse_input(self):
##        toc = TableOfContents(style=toc_style, styles=toc_levels)

        self.content_flowables = []

        self.content_flowables.append(rt.Paragraph(self.root.title.text,
                                                   style='title'))

        for section in self.root.section:
##            toc.register(flowable)
            for flowable in section.parse():
                self.content_flowables.append(flowable)
##        try:
##            for flowable in self.root.body.acknowledgement.parse(self):
##                toc.register(flowable)
##                self.content_flowables.append(flowable)
##        except AttributeError:
##            pass

    def setup(self):
        self.page_count = 1
        self.content = rt.Chain(self)
        page = SimplePage(self)
        self.add_page(page, self.page_count)

        for flowable in self.content_flowables:
            self.content.append_flowable(flowable)

##        bib = self.bibliography.bibliography()
##        self.content.append_flowable(bib)

    def new_page(self, chains):
        page = SimplePage(self)
        self.page_count += 1
        self.add_page(page, self.page_count)
        return page.content
