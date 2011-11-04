
import time

from lxml import etree, objectify

from psg.document.dsc import dsc_document

from pyte.unit import pt
from pyte.paper import Paper
from pyte.layout import Container
from pyte.paragraph import Paragraph
from pyte.layout import EndOfPage


class Orientation:
    Portrait = 0
    Landscape = 1


class Page(Container):
    def __init__(self, document, paper, orientation=Orientation.Portrait):
        assert isinstance(document, Document)
        assert isinstance(paper, Paper)
        self._document = document
        self.paper = paper
        self.orientation = orientation
        if self.orientation is Orientation.Portrait:
            width = self.paper.width
            height = self.paper.height
        else:
            width = self.paper.height
            height = self.paper.width
        super().__init__(None, 0*pt, 0*pt, width, height)

        psg_doc = self.document.psg_doc
        psg_page = psg_doc.page((float(self.width()), float(self.height())))
        self.canvas = psg_page.canvas()

    @property
    def document(self):
        return self._document

    def render(self):
        super().render(self.canvas)


class Document(object):
    def __init__(self, xmlfile, rngschema, lookup):
        self.pages = []

        self.parser = objectify.makeparser(remove_comments=True)
        self.parser.set_element_class_lookup(lookup)

        self.schema = etree.RelaxNG(etree.parse(rngschema))
        self.xml = objectify.parse(xmlfile, self.parser)

        if not self.schema.validate(self.xml):
            err = self.schema.error_log
            raise Exception("XML file didn't pass schema validation:\n%s" % err)
        self.root = self.xml.getroot()

        self.creator = "pyTe"
        self.author = None
        self.title = None
        self.keywords = []
        self.created = time.asctime()

        self.elements = {}
        self.counters = {}

        self.psg_doc = dsc_document(self.title)

    def add_page(self, page, number):
        assert isinstance(page, Page)
        self.pages.append(page)
        page._document = self
        page.number = number

    def render(self, filename):
        for page in self.pages:
            page.render()

        fp = open(filename, "w", encoding="latin-1")
        self.psg_doc.write_to(fp)
        fp.close()

    def add_to_chain(self, chain):
        raise NotImplementedError
