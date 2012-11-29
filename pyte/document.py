
import time
import os
import pickle

from urllib.request import url2pathname

##from lxml import etree, objectify

from pyte.unit import pt
from pyte.paper import Paper
from pyte.layout import Container
from pyte.paragraph import Paragraph
from pyte.layout import EndOfPage
from .util import set_xml_catalog, CATALOG_PATH, CATALOG_URL, CATALOG_NS
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

    @property
    def canvas(self):
        return self.backend_page.canvas

    def render(self):
        backend_document = self.document.backend_document
        self.backend_page = self.backend.Page(self, backend_document,
                                              self.width, self.height)
        end_of_page = None
        try:
            super().render(self.canvas)
        except EndOfPage as e:
            end_of_page = e

        for child in self.children:
            child.place()

        if end_of_page is not None:
            raise end_of_page

    def place(self):
        pass



import xml.etree.ElementTree as ET
from urllib.request import urlopen, pathname2url
from urllib.parse import urlparse, urljoin
from xml.parsers import expat


class ElementTreeParser(ET.XMLParser):
    def __init__(self, lookup):
        target = ET.TreeBuilder(lookup)
        super().__init__(target=target)
        uri_rewrite_map = self.create_uri_rewrite_map()
        self.parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_ALWAYS)
        self.parser.ExternalEntityRefHandler \
            = ExternalEntityRefHandler(self.parser, uri_rewrite_map)

    def create_uri_rewrite_map(self):
        rewrite_map = {}
        catalog = ET.parse(CATALOG_PATH).getroot()
        for elem in catalog.findall('{{{}}}{}'.format(CATALOG_NS,
                                               'rewriteSystem')):
            start_string = elem.get('systemIdStartString')
            prefix = elem.get('rewritePrefix')
            rewrite_map[start_string] = prefix
        return rewrite_map

    def parse(self, xmlfile):
        xml = ET.ElementTree()
        xml.parse(xmlfile, self)
        return xml


class ExternalEntityRefHandler(object):
    def __init__(self, parser, uri_rewrite_map):
        self.parser = parser
        self.uri_rewrite_map = uri_rewrite_map

    def __call__(self, context, base, system_id, public_id):
        if base and not urlparse(system_id).netloc:
            system_id = urljoin(base, system_id)
        # look for local copies of common entity files
        external_parser = self.parser.ExternalEntityParserCreate(context)
        external_parser.ExternalEntityRefHandler \
            = ExternalEntityRefHandler(self.parser, self.uri_rewrite_map)
        for start_string, prefix in self.uri_rewrite_map.items():
            if system_id.startswith(start_string):
                remaining = system_id.split(start_string)[1]
                base = urljoin(CATALOG_URL, prefix)
                system_id = urljoin(base, remaining)
                break
        external_parser.SetBase(system_id)
        with urlopen(system_id) as file:
            external_parser.ParseFile(file)
        return 1


class Document(object):
    cache_extension = '.ptc'

    def __init__(self, xmlfile, rngschema, lookup, backend=psg):
        #set_xml_catalog()
        #self.parser = objectify.makeparser(remove_comments=True,
                                           #no_network=True)
        #self.parser.set_element_class_lookup(lookup)

        #self.schema = etree.RelaxNG(etree.parse(rngschema))
        #self.xml = objectify.parse(xmlfile, self.parser)#, base_url=".")
        #self.xml.xinclude()

        #if not self.schema.validate(self.xml):
            #err = self.schema.error_log
            #raise Exception("XML file didn't pass schema validation:\n%s" % err)
            ## TODO: proper error reporting

        self.parser = ElementTreeParser(lookup)
        self.xml = self.parser.parse(xmlfile)

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
        self._unique_id = 0

    @property
    def unique_id(self):
        self._unique_id += 1
        return self._unique_id

    def load_cache(self, filename):
        try:
            file = open(filename + self.cache_extension, 'rb')
            self.number_of_pages, self.page_references = pickle.load(file)
            self._previous_number_of_pages = self.number_of_pages
            self._previous_page_references = self.page_references.copy()
            file.close()
        except IOError:
            self.number_of_pages = 0
            self._previous_number_of_pages = -1
            self.page_references = {}
            self._previous_page_references = {}

    def save_cache(self, filename):
        file = open(filename + self.cache_extension, 'wb')
        data = (self.number_of_pages, self.page_references)
        pickle.dump(data, file)
        file.close()

    def add_page(self, page, number):
        assert isinstance(page, Page)
        self.pages.append(page)
        page.number = number

    def has_converged(self):
        return (self.number_of_pages == self._previous_number_of_pages and
                self.page_references == self._previous_page_references)

    def render(self, filename):
        self.load_cache(filename)
        self.number_of_pages = self.render_loop()
        while not self.has_converged():
            self._previous_number_of_pages = self.number_of_pages
            self._previous_page_references = self.page_references.copy()
            print('Not yet converged, rendering again...')
            del self.backend_document
            self.backend_document = self.backend.Document(self, self.title)
            self.number_of_pages = self.render_loop()
        self.save_cache(filename)
        print('Writing output: {}'.format(filename +
                                          self.backend_document.extension))
        self.backend_document.write(filename)

    def render_loop(self):
        self.pages = []
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
