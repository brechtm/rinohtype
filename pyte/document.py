
import time

from psg.document.dsc import dsc_document
#from psg.util import *

from pyte.dimension import Dimension
from pyte.unit import pt
from pyte.paper import Paper
from pyte.layout import Container
from pyte.paragraph import Paragraph

class Orientation:
    Portrait = 0
    Landscape = 1


class Page(Container):
    def __init__(self, paper, orientation=Orientation.Portrait):
        assert isinstance(paper, Paper)
        self.paper = paper
        self.orientation = orientation
        if self.orientation is Orientation.Portrait:
            width = self.paper.width
            height = self.paper.height
        else:
            width = self.paper.height
            height = self.paper.width
        Container.__init__(self, None, 0*pt, 0*pt, width, height)

    def render(self, psgDoc):
        #PS_begin_page(psdoc, self.width(), self.height())
        page = psgDoc.page((float(self.width()), float(self.height())))
        thisCanvas = page.canvas()
        thisCanvas._border = True
        Container.render(self, thisCanvas)
        #PS_end_page(psdoc)



class Document(object):
    def __init__(self, filename, title=None):
        self.masterPages = []
        self.pages = []
        self.filename = filename
        self.creator = "pyTe"
        self.author = None
        self.title = title
        self.keywords = []
        self.created = time.asctime()
        self.content = None

    def addMasterPage(self, masterPage):
        assert isinstance(masterpage, Page)
        self.masterPages.append(masterPage)

    def addPage(self, page):
        assert isinstance(page, Page)
        self.pages.append(page)

    def render(self):
        psdoc = dsc_document(self.title)

        for page in self.pages:
            page.render(psdoc)

        fp = open(self.filename, "w", encoding="latin-1")
        psdoc.write_to(fp)
        fp.close()


        #psdoc = PS_new()
        #PS_open_file(psdoc, self.filename)
        #PS_set_info(psdoc, "Creator", self.creator)
        #PS_set_info(psdoc, "Author", self.author)
        #PS_set_info(psdoc, "Title", self.title)
        #PS_set_info(psdoc, "Keywords", ", ".join(self.keywords))
        #for page in self.pages:
        #    page.render(psdoc)
        #PS_close(psdoc)
        #PS_delete(psdoc)

    def __lshift__(self, item):
        assert isinstance(item, Paragraph)
        self.content.addParagraph(item)
        return self

