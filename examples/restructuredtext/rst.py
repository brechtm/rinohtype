
import rinoh as rt

from rinoh.dimension import PT, CM, INCH
from rinoh.backend import pdf
from rinoh.frontend.rst import ReStructuredTextParser


from rinohlib.stylesheets.ieee import styles as ieee_styles


styles = rt.StyleSheet('IEEE for rST', base=ieee_styles)
styles['body'] = rt.ParagraphStyle(base=ieee_styles['body'],
                                   space_below=6*PT)

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
        self.content = rt.Chain(self)
        self.parse_input()

    def parse_input(self):
##        toc = TableOfContents(style=toc_style, styles=toc_levels)
        self.content << rt.Paragraph(self.root.title.text, style='title')

        for section in self.root.section:
##            toc.register(flowable)
            for flowable in section.parse():
                self.content << flowable
##        try:
##            for flowable in self.root.body.acknowledgement.parse(self):
##                toc.register(flowable)
##                self.content_flowables.append(flowable)
##        except AttributeError:
##            pass

    def setup(self):
        self.page_count = 1
        page = SimplePage(self)
        self.add_page(page, self.page_count)
##        bib = self.bibliography.bibliography()
##        self.content.append_flowable(bib)

    def new_page(self, chains):
        page = SimplePage(self)
        self.page_count += 1
        self.add_page(page, self.page_count)
        return page.content
