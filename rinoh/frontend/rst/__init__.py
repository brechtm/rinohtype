# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from docutils.core import publish_doctree
from docutils.parsers.rst import Parser as ReStructuredTextParser

from ...text import MixedStyledText

from .. import (TreeNode, TreeNodeMeta, InlineNode, BodyNode, BodySubNode,
                GroupingNode, DummyNode)


__all__ = ['DocutilsNode', 'DocutilsInlineNode',
           'DocutilsBodyNode', 'DocutilsBodySubNode',
           'DocutilsGroupingNode', 'DocutilsDummyNode',
           'ReStructuredTextReader']


class DocutilsNode(TreeNode, metaclass=TreeNodeMeta):
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
        children_text = (child.styled_text() for child in self.getchildren())
        return MixedStyledText([text for text in children_text if text],
                               style=style)


class DocutilsInlineNode(DocutilsNode, InlineNode):
    @property
    def text(self):
        return super().text.replace('\n', ' ')

    def styled_text(self):
        styled_text = super().styled_text()
        try:
            styled_text.classes = self.get('classes')
        except AttributeError:
            pass
        return styled_text


class DocutilsBodyNode(DocutilsNode, BodyNode):
    def flowables(self):
        classes = self.get('classes')
        for flowable in super().flowables():
            flowable.classes = classes
            yield flowable


class DocutilsBodySubNode(DocutilsNode, BodySubNode):
    pass


class DocutilsGroupingNode(DocutilsBodyNode, GroupingNode):
    pass


class DocutilsDummyNode(DocutilsNode, DummyNode):
    pass


from . import nodes


class DocutilsReader(object):
    parser_class = None

    def parse(self, file):
        filename = getattr(file, 'name', None)
        doctree = publish_doctree(file.read(), source_path=filename,
                                  parser=self.parser_class())
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
        mapped_tree = DocutilsNode.map_node(doctree.document)
        return mapped_tree.children_flowables()


class ReStructuredTextReader(DocutilsReader):
    parser_class = ReStructuredTextParser
