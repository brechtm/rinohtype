
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
        self.section = None

    @property
    def page(self):
        return self

    @property
    def document(self):
        return self._document

    def render(self):
        backend_document = self.document.backend_document
        self.backend_page = self.backend.Page(self, backend_document,
                                              self.width(), self.height())
        self.canvas = self.backend_page.canvas
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
        self.backend_document = self.backend.Document(self, self.title)
        self.counters = {}
        self.elements = {}

    def add_page(self, page, number):
        assert isinstance(page, Page)
        self.pages.append(page)
        page.number = number

    def render(self, filename):
        self.converged = True
        self.number_of_pages = 0
        self._previous_number_of_pages = -1
        self.render_loop()
        while not self.converged:
            print('Not yet converged, rendering again...')
            del self.backend_document
            self.backend_document = self.backend.Document(self, self.title)
            self.number_of_pages = self.render_loop()
            if self.number_of_pages != self._previous_number_of_pages:
                converged = False
                self._previous_number_of_pages = self.number_of_pages
        print('Writing output: {}'.format(filename))
        self.backend_document.write(filename)

    def render_loop(self):
        self.pages = []
        self.converged = True
        self.setup()
        index = 0
        while index < len(self.pages):
            page = self.pages[index]
            index += 1
            try:
                page.render()
            except EndOfPage as e:
                self.add_to_chain(e.args[0])
        return len(self.pages)

    def setup(self):
        raise NotImplementedError

    def add_to_chain(self, chain):
        raise NotImplementedError
