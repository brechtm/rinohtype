# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from importlib import metadata as ilm
from itertools import chain

from ..attribute import AttributesDictionary
from ..flowable import StaticGroupedFlowables
from ..util import NotImplementedAttribute


__all__ = ['TreeNode', 'InlineNode', 'BodyNode', 'BodySubNode', 'GroupingNode',
           'DummyNode', 'TreeNodeMeta', 'Reader']


def find_distribution_for_module(module_name):
    top_level_package_name, *_ = module_name.split('.', maxsplit=1)
    for dist_name in ilm.packages_distributions()[top_level_package_name]:
        print(dist_name)
        dist = ilm.distribution(dist_name)
        for file_path in dist.files:
            if str(file_path).startswith(module_name.replace('.', '/')):
                return dist.name
    return None


class TreeNode(object):
    node_name = None

    @classmethod
    def map_node(cls, node, **context):
        node_name = cls.node_tag_name(node)
        try:
            return cls._mapping[node_name.replace('-', '_')](node, **context)
        except KeyError:
            filename, line, node_name = cls.node_location(node)
            node_module = node.__module__
            node_package, *_ = node_module.split('.', maxsplit=1)
            if node_package in ('docutils', 'sphinx'):
                raise NotImplementedError("{}:{} the '{}' node is not yet "
                    "supported by rinohtype ({}); please report this issue at "
                    "https://github.com/brechtm/rinohtype/issues"
                    .format(filename, line, node_name))
            else:
                distribution_name = find_distribution_for_module(node_module)
                raise RuntimeError("The Sphinx extension '{}' lacks support for"
                                   " the rinoh builder (node '{}')"
                                   .format(distribution_name or '?', node_name))

    def __init__(self, doctree_node, **context):
        self.node = doctree_node
        self.context = context

    def __getattr__(self, name):
        for child in self.getchildren():
            if child.tag_name == name:
                return child
        raise AttributeError('No such element: {} in {}'.format(name, self))

    def __iter__(self):
        try:
            for child in self.parent.getchildren():
                if child.tag_name == self.tag_name:
                    yield child
        except AttributeError:
            # this is the root element
            yield self

    @property
    def tag_name(self):
        return self.node_tag_name(self.node)

    @property
    def parent(self):
        node_parent = self.node_parent(self.node)
        if node_parent is not None:
            return self.map_node(node_parent, **self.context)

    def getchildren(self):
        return [self.map_node(child, **self.context)
                for child in self.node_children(self.node)]

    @property
    def location(self):
        raise NotImplementedError

    @staticmethod
    def node_tag_name(node):
        raise NotImplementedError

    @staticmethod
    def node_parent(node):
        raise NotImplementedError

    @staticmethod
    def node_children(node):
        raise NotImplementedError

    @property
    def text(self):
        raise NotImplementedError

    @property
    def attributes(self):
        return NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def __getitem__(self, name):
        raise NotImplementedError

    def process_content(self, style=None):
        raise NotImplementedError


class InlineNode(TreeNode):
    style = None
    set_id = True

    def styled_text(self, **kwargs):
        styled_text = self.build_styled_text(**kwargs)
        ids = iter(self._ids)
        if self.set_id and self._ids:
            styled_text.id = next(ids)
            for id in ids:
                styled_text.secondary_ids.append(id)
        try:
            styled_text.source = self
        except AttributeError:   # styled_text is None
            pass
        return styled_text

    def build_styled_text(self):
        return self.process_content(style=self.style)


class BodyNodeBase(TreeNode):
    def children_flowables(self, skip_first=0):
        children = self.getchildren()[skip_first:]
        return list(chain(*(item.flowables() for item in children)))


class BodyNode(BodyNodeBase):
    set_id = True

    def flowable(self):
        flowable, = self.flowables()
        return flowable

    def flowables(self):
        ids = iter(self._ids)
        for i, flowable in enumerate(self.build_flowables()):
            if self.set_id and i == 0 and self._ids:
                flowable.id = next(ids)
                for id in ids:
                    flowable.secondary_ids.append(id)
            flowable.source = self
            yield flowable

    def build_flowables(self):
        yield self.build_flowable()

    def build_flowable(self):
        raise NotImplementedError('tag: %s' % self.tag_name)


class BodySubNode(BodyNodeBase):
    def process(self):
        raise NotImplementedError('tag: %s' % self.tag_name)


class GroupingNode(BodyNode):
    style = None
    grouped_flowables_class = StaticGroupedFlowables

    def build_flowable(self, style=None, **kwargs):
        return self.grouped_flowables_class(self.children_flowables(),
                                            style=style or self.style,
                                            **kwargs)


class DummyNode(BodyNode, InlineNode):
    def flowables(self):    # empty generator
        return
        yield

    def styled_text(self, preserve_space=False):
        return None


class TreeNodeMeta(type):
    root = TreeNode
    bases = InlineNode, BodyNode, BodySubNode, GroupingNode, DummyNode

    def __new__(metaclass, name, bases, namespace):
        cls = super().__new__(metaclass, name, bases, namespace)
        node_name = cls.node_name or name.lower()
        if metaclass.root in bases:
            cls._mapping = {}
            cls._base_class = cls
        elif set(bases).isdisjoint(set(metaclass.bases)):
            cls._mapping[node_name] = cls
        return cls


class Reader(AttributesDictionary):
    extensions = NotImplementedAttribute()

    def __getitem__(self, name):
        return getattr(self, name)
