
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
    Parser = xml_frontend.Parser
    CustomElement = xml_frontend.CustomElement
except ImportError:
    try:
        from .lxml import Parser, CustomElement
    except ImportError:
        from .elementtree import Parser, CustomElement


class NestedElement(CustomElement):
    def parse(self, document):
        content = self.text or ''
        for child in self.getchildren():
            content += child.parse(document)
            if child.tail is not None:
                content += child.tail
        return content
