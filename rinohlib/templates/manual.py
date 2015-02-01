

from rinoh.document import Document, Page, PORTRAIT
from rinoh.dimension import PT, CM
from rinoh.layout import Container, FootnoteContainer, Chain
from rinoh.paper import A5


# page definition
# ----------------------------------------------------------------------------

class SimplePage(Page):
    topmargin = bottommargin = 2*CM
    leftmargin = rightmargin = 2*CM

    def __init__(self, document):
        super().__init__(document, A5, PORTRAIT)

        body_width = self.width - (self.leftmargin + self.rightmargin)
        body_height = self.height - (self.topmargin + self.bottommargin)
        self.body = Container('body', self, self.leftmargin, self.topmargin,
                              body_width, body_height)

        self.footnote_space = FootnoteContainer('footnotes', self.body, 0*PT,
                                                   body_height)
        self.content = Container('content', self.body, 0*PT, 0*PT,
                                 bottom=self.footnote_space.top,
                                 chain=document.content)

        self.content._footnote_space = self.footnote_space


# main document
# ----------------------------------------------------------------------------
class Manual(Document):
    def __init__(self, rinoh_tree, stylesheet, backend=None, title=None):
        super().__init__(stylesheet, backend=backend, title=title)
        self.content = Chain(self)

        # TODO: move to superclass
        for child in rinoh_tree.getchildren():
            self.content << child.flowable()

    def setup(self):
        self.page_count = 1
        page = SimplePage(self)
        self.add_page(page, self.page_count)

    def new_page(self, chains):
        page = SimplePage(self)
        self.page_count += 1
        self.add_page(page, self.page_count)
        return page.content
