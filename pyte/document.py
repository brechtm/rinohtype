
import time

from lxml import etree, objectify

from pyte.unit import pt
from pyte.paper import Paper
from pyte.layout import Container
from pyte.paragraph import Paragraph
from pyte.layout import EndOfPage
from .util import set_xml_catalog
from .backend import psg


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

        self.backend = self.document.backend
        backend_document = self.document.backend_document
        self.backend_page = self.backend.Page(self, backend_document,
                                              width, height)
        self.canvas = self.backend_page.canvas

    @property
    def document(self):
        return self._document

    def render(self):
        super().render(self.canvas)


class Document(object):
    def __init__(self, xmlfile, rngschema, lookup, backend=psg):
        set_xml_catalog()
        self.parser = objectify.makeparser(remove_comments=True,
                                           no_network=True)
        self.parser.set_element_class_lookup(lookup)

        self.schema = etree.RelaxNG(etree.parse(rngschema))
        self.xml = objectify.parse(xmlfile, self.parser)#, base_url=".")

        if not self.schema.validate(self.xml):
            err = self.schema.error_log
            raise Exception("XML file didn't pass schema validation:\n%s" % err)
            # TODO: proper error reporting
        self.root = self.xml.getroot()

        self.creator = "pyTe"
        self.author = None
        self.title = None
        self.keywords = []
        self.created = time.asctime()

        self.backend = backend
        self.backend_document = backend.Document(self, self.title)

    def add_page(self, page, number):
        assert isinstance(page, Page)
        self.pages.append(page)
        page._document = self
        page.number = number

    def render(self, filename):
        self.elements = {}
        self.converged = True
        self.render_loop()
        self.backend_document.write(filename)

    def render_loop(self):
        self.counters = {}
        self.pages = []
        self.converged = True
        self.setup()
        for page in self.pages:
            try:
                page.render()
            except EndOfPage as e:
                self.add_to_chain(e.args[0])

    def setup(self):
        raise NotImplementedError

    def add_to_chain(self, chain):
        raise NotImplementedError
