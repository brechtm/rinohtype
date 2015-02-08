

from rinoh.document import Document, Page, PORTRAIT
from rinoh.dimension import PT, CM
from rinoh.layout import Container, FootnoteContainer, Chain
from rinoh.paper import A4


# page definition
# ----------------------------------------------------------------------------

class SimplePage(Page):
    topmargin = bottommargin = 2*CM
    leftmargin = rightmargin = 2*CM

    def __init__(self, document, paper, orientation):
        super().__init__(document, paper, orientation)

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
    def __init__(self, rinoh_tree, stylesheet, options=None, backend=None,
                 title=None):
        super().__init__(stylesheet, backend=backend, title=title)
        self.options = options or ManualOptions()
        self.content = Chain(self)

        # TODO: move to superclass
        for child in rinoh_tree.getchildren():
            self.content << child.flowable()

    def setup(self):
        self.page_count = 0
        self.new_page(set())

    def new_page(self, chains):
        page = SimplePage(self, self.options['page_size'],
                          self.options['page_orientation'])
        self.page_count += 1
        self.add_page(page, self.page_count)
        return page.content


class ManualOptions(dict):
    options = {'page_size': A4,
               'page_orientation': PORTRAIT}

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
