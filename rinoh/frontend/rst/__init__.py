
from docutils.core import publish_doctree

from rinoh.util import all_subclasses


class CustomElement(object):
    def __init__(self, doctree_node):
        self.node = doctree_node

    def __getattr__(self, name):
        for child in self.node.children:
            if child.tagname == name:
                return map_node(child)
        raise AttributeError('No such element: {}'.format(name))

    def __iter__(self):
        try:
            for child in self.parent.node.children:
                if child.tagname == self.node.tagname:
                    yield map_node(child)
        except AttributeError:
            # this is the root element
            yield self

    @property
    def parent(self):
        if self.node.parent is not None:
            return map_node(self.node.parent)

    @property
    def text(self):
        return self.node.astext()

    def get(self, key, default=None):
        return self.node.get(key, default)

    def getchildren(self):
        return [map_node(child) for child in self.node.children]

    def process(self, *args, **kwargs):
        result = self.parse(*args, **kwargs)
        try:
            result.source = self
        except AttributeError:
            pass
        return result

    def parse(self, *args, **kwargs):
        raise NotImplementedError('tag: %s' % self.tag)

    @property
    def location(self):
        return '{}: <{}> at line {}'.format(self.node.source,
                                            self.node.tagname,
                                            self.node.line)


class NestedElement(CustomElement):
    def parse(self, *args, **kwargs):
        return self.process_content()

    def process_content(self):
        content = ''
        for child in self.getchildren():
            content += child.process()
        return content


from . import nodes


MAPPING = {cls.__name__.lower(): cls for cls in all_subclasses(CustomElement)}
MAPPING['Text'] = nodes.Text


def map_node(node):
    return MAPPING[node.__class__.__name__](node)


class ReStructuredTextParser(object):
    def parse(self, filename):
        with open(filename) as file:
            doctree = publish_doctree(file.read(), source_path=filename)
        return map_node(doctree.document)
