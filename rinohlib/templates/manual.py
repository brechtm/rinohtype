

from rinoh.document import Document, DocumentPart, Page, PORTRAIT
from rinoh.dimension import PT, CM
from rinoh.layout import Container, FootnoteContainer, Chain
from rinoh.paper import A4

from rinoh.structure import Section, Heading, TableOfContents


# page definition
# ----------------------------------------------------------------------------

class SimplePage(Page):
    topmargin = bottommargin = 2*CM
    leftmargin = rightmargin = 2*CM

    def __init__(self, chain, paper, orientation):
        super().__init__(chain.document, paper, orientation)

        body_width = self.width - (self.leftmargin + self.rightmargin)
        body_height = self.height - (self.topmargin + self.bottommargin)
        self.body = Container('body', self, self.leftmargin, self.topmargin,
                              body_width, body_height)

        self.footnote_space = FootnoteContainer('footnotes', self.body, 0*PT,
                                                body_height)
        self.content = Container('content', self.body, 0*PT, 0*PT,
                                 bottom=self.footnote_space.top,
                                 chain=chain)

        self.content._footnote_space = self.footnote_space


# document parts
# ----------------------------------------------------------------------------

# class TitlePart(DocumentPart)



class ManualPart(DocumentPart):
    def __init__(self, document):
        super().__init__(document)
        self.chain = Chain(document)

    def init(self):
        self.new_page([self.chain])

    def new_page(self, chains):
        assert (len(chains) == 1)
        page = SimplePage(next(iter(chains)),
                          self.document.options['page_size'],
                          self.document.options['page_orientation'])
        self.page_count += 1
        self.add_page(page, self.page_count)
        return page.content


class TableOfContentsPart(ManualPart):
    def __init__(self, document):
        super().__init__(document)
        self.chain << Section([Heading('Table of Contents', style='unnumbered'),
                               TableOfContents()])


class ContentsPart(ManualPart):
    def __init__(self, document, content_tree):
        super().__init__(document)
        for child in content_tree.getchildren():
            self.chain << child.flowable()


# main document
# ----------------------------------------------------------------------------
class Manual(Document):
    def __init__(self, rinoh_tree, stylesheet, options=None, backend=None,
                 title=None):
        super().__init__(stylesheet, backend=backend, title=title)
        self.options = options or ManualOptions()
        self.add_part(TableOfContentsPart(self))
        self.add_part(ContentsPart(self, rinoh_tree))


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
