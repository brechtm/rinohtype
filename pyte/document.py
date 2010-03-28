
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
        page = psgDoc.page((float(self.width()), float(self.height())))
        thisCanvas = page.canvas()
        thisCanvas._border = True
        Container.render(self, thisCanvas)


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

    def __lshift__(self, item):
        assert isinstance(item, Paragraph)
        self.content.addParagraph(item)
        return item

    def addMasterPage(self, masterPage):
        assert isinstance(masterpage, Page)
        self.masterPages.append(masterPage)

    def addPage(self, page):
        assert isinstance(page, Page)
        self.pages.append(page)

    def render(self):
        psgDoc = dsc_document(self.title)

        # TODO: generate pages as required (based on master pages
        # http://docs.python.org/tutorial/classes.html#generators
        for page in self.pages:
            print(page)
            page.render(psgDoc)

        fp = open(self.filename, "w", encoding="latin-1")
        psgDoc.write_to(fp)
        fp.close()
