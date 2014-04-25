
from docutils.core import publish_doctree

from rinoh.text import MixedStyledText
from rinoh.flowable import StaticGroupedFlowables
from rinoh.util import all_subclasses


class CustomElement(object):
    @classmethod
    def map_node(cls, node):
        return cls.MAPPING[node.__class__.__name__](node)

    def __init__(self, doctree_node):
        self.node = doctree_node

    def __getattr__(self, name):
        for child in self.node.children:
            if child.tagname == name:
                return self.map_node(child)
        raise AttributeError('No such element: {}'.format(name))

    def __getitem__(self, name):
        return self.node[name]

    def __iter__(self):
        try:
            for child in self.parent.node.children:
                if child.tagname == self.node.tagname:
                    yield self.map_node(child)
        except AttributeError:
            # this is the root element
            yield self

    @property
    def parent(self):
        if self.node.parent is not None:
            return self.map_node(self.node.parent)

    @property
    def text(self):
        return self.node.astext()

    def get(self, key, default=None):
        return self.node.get(key, default)

    def getchildren(self):
        return [self.map_node(child) for child in self.node.children]

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
        content = MixedStyledText([])
        for child in self.getchildren():
            content += child.process()
        return content


class GroupingElement(CustomElement):
    style = None

    def parse(self):
        return StaticGroupedFlowables([item.process()
                                       for item in self.getchildren()],
                                      style=self.style)


from . import nodes

CustomElement.MAPPING = {cls.__name__.lower(): cls
                         for cls in all_subclasses(CustomElement)}
CustomElement.MAPPING['Text'] = nodes.Text


class ReStructuredTextParser(object):
    def parse(self, filename):
        with open(filename) as file:
            doctree = publish_doctree(file.read(), source_path=filename)
        return CustomElement.map_node(doctree.document)
