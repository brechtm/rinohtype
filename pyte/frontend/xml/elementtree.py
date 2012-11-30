
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen, pathname2url
from warnings import warn
from xml.parsers import expat
from xml.etree import ElementTree

from . import  CATALOG_PATH, CATALOG_URL, CATALOG_NS


class Parser(ElementTree.XMLParser):
    def __init__(self, namespace, schema=None):
        if schema:
            warn('The ElementTree based XML parser does not support '
                 'validation. Please install lxml in order to enable '
                 'validation.')
        self.namespace = '{{{}}}'.format(namespace)
        self.element_classes = {self.namespace + cls.__name__.lower(): cls
                                for cls in CustomElement.__subclasses__()}
        tree_builder = ElementTree.TreeBuilder(self.lookup)
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
        xml._namespace = self.namespace
        xml._parent_map = dict((c, p) for p in xml.getiterator() for c in p)
        for elem in xml.getiterator():
            elem._tree = xml
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


class ObjectifiedElement(object):
    """Simulation of lxml.objectify.ObjectifiedElement using xml.ElementTree"""
    def __init__(self, tag, attrib={}, **extra):
        self._element = ElementTree.Element(tag, attrib, **extra)

    @property
    def tag(self):
        return self._element.tag

    @property
    def text(self):
        return self._element.text

    @text.setter
    def text(self, value):
        self._element.text = value

    @property
    def tail(self):
        return self._element.tail

    @tail.setter
    def tail(self, value):
        self._element.tail = value

    def __getattr__(self, name):
        result = self._element.find(self._element._tree._namespace + name)
        if result is None:
            raise AttributeError('No such element: {}'.format(name))
        return result

    def __iter__(self):
        parent = self._element._tree._parent_map[self]
        for child in parent.findall(self.tag):
            yield child

    def append(self, item):
        self._element.append(item)

    def iter(self, tag):
        return self._element.iter(tag)

    def get(self, key, default=None):
        return self._element.get(key, default)

    def getchildren(self):
        return self._element.getchildren()


class CustomElement(ObjectifiedElement):
    def parse(self, document):
        raise NotImplementedError('tag: %s' % self.tag)
