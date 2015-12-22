# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import sys

from urllib.parse import urlparse, urljoin
from urllib.request import urlopen
from warnings import warn
from xml.parsers import expat

# this module depends on internals of the Python ElementTree implementation, so
# we can't use the C accelerated versions (which are the default in Python 3.3+)
_cached_etree_modules = {}
for name in list(sys.modules.keys()):
    if name.startswith('xml.etree') or name == '_elementtree':
        _cached_etree_modules[name] = sys.modules.pop(name)
sys.modules['_elementtree'] = None

from xml.etree import ElementTree, ElementPath

for name in list(sys.modules.keys()):
    if name.startswith('xml.etree'):
        del sys.modules[name]
sys.modules.update(_cached_etree_modules)

from . import CATALOG_PATH, CATALOG_URL, CATALOG_NS


class TreeBuilder(ElementTree.TreeBuilder):
    def __init__(self, namespace, line_callback, element_factory=None):
        super().__init__(element_factory)
        self._namespace = namespace
        self._line_callback = line_callback

    def start(self, tag, attrs):
        elem = super().start(tag, attrs)
        elem.sourceline = self._line_callback()
        return elem

    def end(self, tag):
        last = super().end(tag)
        try:
            last._parent = self._elem[-1]
            last._root = self._elem[0]
        except IndexError:
            last._parent = None
            last._root = self
        last._namespace = self._namespace
        return last


class Parser(ElementTree.XMLParser):
    def __init__(self, element_class, namespace=None, schema=None):
        self.element_class = element_class
        if schema:
            warn('The ElementTree based XML parser does not support '
                 'validation. Please use the lxml frontend if you require '
                 'validation.')
        self.namespace = '{{{}}}'.format(namespace) if namespace else ''
        tree_builder = TreeBuilder(self.namespace, self.get_current_line_number)
        super().__init__(target=tree_builder)
        # uri_rewrite_map = self.create_uri_rewrite_map()
        # self.parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_ALWAYS)
        # self.parser.ExternalEntityRefHandler \
        #     = ExternalEntityRefHandler(self.parser, uri_rewrite_map)

    def get_current_line_number(self):
        return self.parser.CurrentLineNumber

    def create_uri_rewrite_map(self):
        rewrite_map = {}
        catalog = ElementTree.parse(CATALOG_PATH).getroot()
        for elem in catalog.findall('{{{}}}{}'.format(CATALOG_NS,
                                               'rewriteSystem')):
            start_string = elem.get('systemIdStartString')
            prefix = elem.get('rewritePrefix')
            rewrite_map[start_string] = prefix
        return rewrite_map

    def parse(self, xmlfile):
        xml = ElementTree.ElementTree()
        xml.parse(xmlfile, self)
        xml._filename = xmlfile
        xml.getroot()._roottree = xml
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
