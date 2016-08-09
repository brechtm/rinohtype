# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ..xml.elementtree import Parser
from ..xml import (ElementTreeNode, ElementTreeInlineNode, ElementTreeBodyNode,
                   ElementTreeBodySubNode, ElementTreeGroupingNode,
                   ElementTreeDummyNode, ElementTreeNodeMeta)


__all__ = ['DocBookNode', 'DocBookInlineNode', 'DocBookBodyNode',
           'DocBookBodySubNode', 'DocBookGroupingNode', 'DocBookDummyNode',
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


class DocBookDummyNode(DocBookNode, ElementTreeDummyNode):
    pass


from . import nodes


class DocBookReader(object):
    rngschema = None
    namespace = DocBookNode.NAMESPACE

    def parse(self, file):
        filename = getattr(file, 'name', None)
        parser = Parser(DocBookNode, #namespace=self.namespace,
                        schema=self.rngschema)
        xml_tree = parser.parse(filename)
        doctree = xml_tree.getroot()
        return self.from_doctree(doctree)

    def from_doctree(self, doctree):
        mapped_tree = DocBookNode.map_node(doctree)
        return mapped_tree.children_flowables()
