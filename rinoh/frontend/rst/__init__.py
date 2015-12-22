# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from docutils.core import publish_doctree

from ...text import MixedStyledText

from .. import (TreeNode, InlineNode, BodyNode, BodySubNode, GroupingNode,
                DummyNode)

__all__ = ['ReStructuredTextNode', 'ReStructuredTextInlineNode',
           'ReStructuredTextBodyNode', 'ReStructuredTextBodySubNode',
           'ReStructuredTextGroupingNode', 'ReStructuredTextDummyNode',
           'ReStructuredTextParser']


class ReStructuredTextNode(TreeNode):
    @staticmethod
    def node_tag_name(node):
        return node.tagname

    @staticmethod
    def node_parent(node):
        return node.parent

    @staticmethod
    def node_children(node):
        return node.children

    @property
    def _id(self):
        try:
            return self.get('ids')[0]
        except IndexError:
            return None

    @property
    def _location(self):
        return self.node.source, self.node.line, self.tag_name

    @property
    def text(self):
        return self.node.astext()

    @property
    def attributes(self):
        return self.node.attributes

    def get(self, key, default=None):
        return self.node.get(key, default)

    def __getitem__(self, name):
        return self.node[name]

    def process_content(self, style=None):
        preserve_space = self.get('xml:space', None) == 'preserve'
        return MixedStyledText([text
                                for text in (child.styled_text(preserve_space)
                                             for child in self.getchildren())
                                if text], style=style)


class ReStructuredTextInlineNode(ReStructuredTextNode, InlineNode):
    @property
    def text(self):
        return super().text.replace('\n', ' ')

    def styled_text(self, preserve_space=False):
        styled_text = super().styled_text(preserve_space=preserve_space)
        try:
            styled_text.classes = self.get('classes')
        except AttributeError:
            pass
        return styled_text


class ReStructuredTextBodyNode(ReStructuredTextNode, BodyNode):
    def flowables(self):
        classes = self.get('classes')
        for flowable in super().flowables():
            flowable.classes = classes
            yield flowable


class ReStructuredTextBodySubNode(ReStructuredTextNode, BodySubNode):
    pass


class ReStructuredTextGroupingNode(ReStructuredTextBodyNode, GroupingNode):
    pass


class ReStructuredTextDummyNode(ReStructuredTextNode, DummyNode):
    pass


from . import nodes


class ReStructuredTextParser(object):
    def parse(self, file):
        filename = getattr(file, 'name', None)
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
        mapped_tree = ReStructuredTextNode.map_node(doctree.document)
        return mapped_tree.children_flowables()
