
import time

from lxml import etree, objectify

from psg.document.dsc import dsc_document
#from psg.util import *

from pyte.dimension import Dimension
from pyte.unit import pt
from pyte.paper import Paper
from pyte.layout import Container
from pyte.paragraph import Paragraph
from pyte.structure import Heading
from pyte.layout import EndOfPage

class Orientation:
    Portrait = 0
    Landscape = 1

PORTRAIT = Orientation.Portrait
LANDSCAPE = Orientation.Landscape

class Page(Container):
    def __init__(self, psg_doc, paper, orientation=Orientation.Portrait):
        assert isinstance(paper, Paper)
        self.paper = paper
        self.orientation = orientation
        if self.orientation is Orientation.Portrait:
            width = self.paper.width
            height = self.paper.height
        else:
            width = self.paper.height
            height = self.paper.width
        super().__init__(None, 0*pt, 0*pt, width, height)

        psg_page = psg_doc.page((float(self.width()), float(self.height())))
        self.canvas = psg_page.canvas()
        self.canvas._border = True

        #---
##        dimensions = (float(self.width()), float(self.height()))
##        psg_page = self.document.psg_doc.page(dimensions)
##        self.canvas = psg_page.canvas()
##        self.canvas._border = True

    def render(self):
        print(self.paragraphs())
        super().render(self.canvas)


class Document(object):
    default = None

    def __init__(self, filename, xmlfile, rngschema, lookup):
        self.filename = filename
        self.pages = []

        self.parser = objectify.makeparser()
        #self.parser = etree.XMLParser()
        self.parser.set_element_class_lookup(lookup)

        self.schema = etree.RelaxNG(etree.parse(rngschema))
        self.xml = objectify.parse(xmlfile, self.parser)
        #self.xml = objectify.parse(xmlfile)
        #self.xml = etree.parse(xmlfile, self.parser)

        if not self.schema.validate(self.xml):
            err = self.schema.error_log
            raise Exception("XML file didn't pass schema validation:\n%s" % err)
        self.root = self.xml.getroot()

        self.creator = "pyTe"
        self.author = None
        self.title = None
        self.keywords = []
        self.created = time.asctime()

        self.headingLevel = 1
        self.listLevel = 1

        self.psg_doc = dsc_document(self.title)

        Document.default = self

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
        page.document = self

    def render(self):
##        currentpage = next(self.pagegen)
##        for item in self.content:
##            try:
##                currentpage.content.render(item)
##            except EndOfPage:
##                currentpage = next(self.pagegen)
##
        # TODO: generate pages as required (based on master pages
        # http://docs.python.org/tutorial/classes.html#generators
        for page in self.pages:
            print(page)
            try:
                page.render()
            except EndOfPage:
                self.addPage(next(self.pagegen))
                print("EndOfPage")
                continue
##            except EndOfContent:
##                break

        fp = open(self.filename, "w", encoding="latin-1")
        self.psg_doc.write_to(fp)
        fp.close()
