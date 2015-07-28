# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from functools import wraps

from docutils.core import publish_doctree

from rinoh.text import MixedStyledText
from rinoh.flowable import StaticGroupedFlowables
from rinoh.style import PARENT_STYLE
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
    def attributes(self):
        return self.node.attributes

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

    def process_content(self, style=None):
        preserve_space = self.get('xml:space', None) == 'preserve'
        return MixedStyledText([text
                                for text in (child.styled_text(preserve_space)
                                             for child in self.getchildren())
                                if text], style=style)

    @property
    def location(self):
        return '{}:{} <{}>'.format(self.node.source, self.node.line,
                                   self.node.tagname)


def set_source(method):
    """Decorator that sets the `source` attribute of the returned object to
    `self`"""
    @wraps(method)
    def method_wrapper(obj, *args, **kwargs):
        result = method(obj, *args, **kwargs)
        try:
            result.source = obj
        except AttributeError:
            pass
        return result
    return method_wrapper


class BodyElement(CustomElement):
    @set_source
    def flowable(self):
        flowable = self.build_flowable()
        ids = self.get('ids')
        if ids:
            flowable.id = ids[0]
        flowable.classes = self.get('classes')
        return flowable

    def build_flowable(self):
        raise NotImplementedError('tag: %s' % self.tag)


class BodySubElement(CustomElement):
    def process(self):
        raise NotImplementedError('tag: %s' % self.tag)


class InlineElement(CustomElement):
    @property
    def text(self):
        return super().text.replace('\n', ' ')

    @set_source
    def styled_text(self, preserve_space=False):
        styled_text = self.build_styled_text()
        try:
            styled_text.classes = self.get('classes')
        except AttributeError:
            pass
        return styled_text

    def build_styled_text(self):
        raise NotImplementedError('tag: %s' % self.tag)


class GroupingElement(BodyElement):
    style = None
    grouped_flowables_class = StaticGroupedFlowables

    def build_flowable(self, **kwargs):
        flowables = [item.flowable() for item in self.getchildren()]
        return self.grouped_flowables_class(flowables,
                                            style=self.style, **kwargs)


from . import nodes

CustomElement.MAPPING = {cls.__name__.lower(): cls
                         for cls in all_subclasses(CustomElement)}
CustomElement.MAPPING['Text'] = nodes.Text


class ReStructuredTextParser(object):
    def parse(self, filename):
        with open(filename) as file:
            doctree = publish_doctree(file.read(), source_path=filename)
        return self.from_doctree(doctree)

    @staticmethod
    def replace_secondary_ids(tree):
        id_aliases = {}
        for node in tree.traverse():
            try:
                primary_id, *alias_ids = node.attributes['ids']
                for alias_id in alias_ids:
                    id_aliases[alias_id] = primary_id
            except (AttributeError, KeyError, ValueError):
                pass
        # replace alias IDs used in references with the corresponding primary ID
        for node in tree.traverse():
            try:
                refid = node.get('refid')
                if refid in id_aliases:
                    node.attributes['refid'] = id_aliases[refid]
            except AttributeError:
                pass

    def from_doctree(self, doctree):
        self.replace_secondary_ids(doctree)
        mapped_tree = CustomElement.map_node(doctree.document)
        flowables = [child.flowable() for child in mapped_tree.getchildren()]
        return flowables
