# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ..xml.elementtree import Parser
from ..xml import (ElementTreeNode, ElementTreeInlineNode, ElementTreeBodyNode,
                   ElementTreeBodySubNode, ElementTreeGroupingNode,
                   ElementTreeDummyNode)


class DITANode(ElementTreeNode):
    pass


class DITAInlineNode(DITANode, ElementTreeInlineNode):
    pass


class DITABodyNode(DITANode, ElementTreeBodyNode):
    pass


class DITABodySubNode(DITANode, ElementTreeBodySubNode):
    pass


class DITAGroupingNode(DITANode, ElementTreeGroupingNode):
    pass


class DITADummyNode(DITANode, ElementTreeDummyNode):
    pass


from . import nodes


class DITAReader(object):
    def parse(self, file):
        filename = getattr(file, 'name', None)
        parser = Parser(DITANode)
        xml_tree = parser.parse(filename)
        doctree = xml_tree.getroot()
        return self.from_doctree(doctree)

    def from_doctree(self, doctree):
        mapped_tree = DITANode.map_node(doctree)
        return mapped_tree.tree()
