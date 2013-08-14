# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from urllib.parse import urlparse, urljoin
from urllib.request import urlopen, pathname2url
from warnings import warn
from xml.parsers import expat
from xml.etree import ElementTree, ElementPath

from ...util import all_subclasses
from . import CATALOG_PATH, CATALOG_URL, CATALOG_NS


class TreeBuilder(ElementTree.TreeBuilder):
    def __init__(self, namespace, element_factory=None):
        super().__init__(element_factory)
        self._namespace = namespace

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
        self.element_classes = {self.namespace + cls.__name__.lower(): cls
                                for cls in all_subclasses(self.element_class)}
        tree_builder = TreeBuilder(self.namespace, self.lookup)
        super().__init__(target=tree_builder)
        uri_rewrite_map = self.create_uri_rewrite_map()
        self.parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_ALWAYS)
        self.parser.ExternalEntityRefHandler \
            = ExternalEntityRefHandler(self.parser, uri_rewrite_map)

    def lookup(self, tag, attrs):
        try:
            return self.element_classes[tag](tag, attrs)
        except KeyError:
            return self.element_class(tag, attrs)

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

    # store source line for each element (http://bugs.python.org/issue14078)
    def _start_list(self, *args, **kwargs):
        element = super()._start_list(*args, **kwargs)
        element.sourceline = self._parser.CurrentLineNumber
        return element


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


class ObjectifiedElement(ElementTree.Element):
    """Simulation of lxml's ObjectifiedElement for xml.etree"""
    def __getattr__(self, name):
        # the following depends on ElementPath internals, but should be fine
        result = ElementPath.find(self.getchildren(), self._namespace + name)
        if result is None:
            raise AttributeError('No such element: {}'.format(name))
        return result

    def __iter__(self):
        try:
            # same hack as above
            for child in ElementPath.findall(self._parent.getchildren(),
                                             self.tag):
                yield child
        except AttributeError:
            # this is the root element
            yield self


class BaseElement(ObjectifiedElement):
    @property
    def filename(self):
        return self._root._roottree._filename
