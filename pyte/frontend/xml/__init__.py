
import os

from importlib import import_module
from urllib.parse import urljoin
from urllib.request import pathname2url

from ... import DATA_PATH


CATALOG_PATH = os.path.join(DATA_PATH, 'xml', 'catalog')
CATALOG_URL = urljoin('file:', pathname2url(CATALOG_PATH))
CATALOG_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"


try:
    from .. import XML_FRONTEND
    xml_frontend = import_module(XML_FRONTEND)
except ImportError:
    try:
        from . import lxml as xml_frontend
    except ImportError:
        from . import elementtree as xml_frontend


class CustomElement(xml_frontend.BaseElement):
    def process(self, document, *args, **kwargs):
        result = self.parse(document, *args, **kwargs)
        try:
            result._source = self
        except AttributeError:
            pass
        return result

    def parse(self, document, *args, **kwargs):
        raise NotImplementedError('tag: %s' % self.tag)

    @property
    def location(self):
        tag = self.tag.split('}', 1)[1] if '}' in self.tag else self.tag
        return '{}: <{}> at line {}'.format(self.filename, tag, self.sourceline)


class NestedElement(CustomElement):
    def parse(self, document, *args, **kwargs):
        return self.process_content(document)

    def process_content(self, document):
        content = self.text
        for child in self.getchildren():
            content += child.process(document) + child.tail
        return content


Parser = xml_frontend.Parser
Parser.element_class = CustomElement
