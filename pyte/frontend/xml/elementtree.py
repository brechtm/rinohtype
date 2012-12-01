
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen, pathname2url
from warnings import warn
from xml.parsers import expat
from xml.etree import ElementTree, ElementPath

from . import  CATALOG_PATH, CATALOG_URL, CATALOG_NS


class TreeBuilder(ElementTree.TreeBuilder):
    def __init__(self, namespace, element_factory=None):
        super().__init__(element_factory)
        self._namespace = namespace

    def end(self, tag):
        last = super().end(tag)
        try:
            last._parent = self._elem[-1]
        except IndexError:
            last._parent = None
        last._namespace = self._namespace
        return last


class Parser(ElementTree.XMLParser):
    def __init__(self, namespace, schema=None):
        if schema:
            warn('The ElementTree based XML parser does not support '
                 'validation. Please install lxml in order to enable '
                 'validation.')
        self.namespace = '{{{}}}'.format(namespace)
        self.element_classes = {self.namespace + cls.__name__.lower(): cls
                                for cls in CustomElement.__subclasses__()}
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
            return CustomElement(tag, attrs)

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


class ObjectifiedElement(ElementTree.Element):
    """Simulation of lxml's ObjectifiedElement for xml.etree"""
    def __getattr__(self, name):
        # the following depends on ElementPath internals, but should be fine
        result = ElementPath.find(self.getchildren(),
                                  self._namespace + name)
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


class CustomElement(ObjectifiedElement):
    def parse(self, document):
        raise NotImplementedError('tag: %s' % self.tag)
