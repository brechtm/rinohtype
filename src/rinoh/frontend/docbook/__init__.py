# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ..xml.elementtree import Parser
from ..xml import (ElementTreeNode, ElementTreeInlineNode, ElementTreeBodyNode,
                   ElementTreeBodySubNode, ElementTreeGroupingNode,
                   ElementTreeMixedContentNode, ElementTreeDummyNode, ElementTreeNodeMeta)

from ...document import DocumentTree

from os import path


__all__ = ['DocBookNode', 'DocBookInlineNode', 'DocBookBodyNode',
           'DocBookBodySubNode', 'DocBookGroupingNode', 'DocBookMixedContentNode', 'DocBookDummyNode',
           'DocBookReader']


class DocBookNode(ElementTreeNode, metaclass=ElementTreeNodeMeta):
    NAMESPACE = 'http://docbook.org/ns/docbook'


class DocBookInlineNode(DocBookNode, ElementTreeInlineNode):
    pass


class DocBookBodyNode(DocBookNode, ElementTreeBodyNode):
    pass


class DocBookBodySubNode(DocBookNode, ElementTreeBodySubNode):
    pass


class DocBookGroupingNode(DocBookNode, ElementTreeGroupingNode):
    pass


class DocBookMixedContentNode(DocBookNode, ElementTreeMixedContentNode):
    pass


class DocBookDummyNode(DocBookNode, ElementTreeDummyNode):
    pass


from . import nodes


class DocBookReader(object):
    rngschema = None
    namespace = DocBookNode.NAMESPACE

    def parse(self, file):
        parser = Parser(DocBookNode, #namespace=self.namespace,
                        schema=self.rngschema)
        doctree = parser.parse(file)
        return self.from_doctree(doctree)

    def from_doctree(self, doctree):
        mapped_tree = DocBookNode.map_node(doctree)
        return DocumentTree(mapped_tree.children_flowables())
