# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from docutils.core import publish_doctree
from docutils.parsers.rst import Parser as ReStructuredTextParser

from ...document import DocumentTree
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
    def _ids(self):
        return self.get('ids')

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
        return self.from_doctree(filename, doctree)

    def from_doctree(self, filename, doctree):
        mapped_tree = DocutilsNode.map_node(doctree.document)
        flowables = mapped_tree.children_flowables()
        return DocumentTree(filename, flowables)


class ReStructuredTextReader(DocutilsReader):
    parser_class = ReStructuredTextParser
