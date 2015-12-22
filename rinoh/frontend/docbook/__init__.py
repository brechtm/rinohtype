# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import re

from itertools import chain

from ..xml import elementtree, ElementTreeNode

from ...flowable import StaticGroupedFlowables


class DocBookNode(ElementTreeNode):
    NAMESPACE = 'http://docbook.org/ns/docbook'


class BodyElementBase(DocBookNode):
    def children_flowables(self, skip_first=0):
        children = self.getchildren()[skip_first:]
        return list(chain(*(item.flowables() for item in children)))


class BodyElement(BodyElementBase):
    def flowable(self):
        flowable, = self.flowables()
        return flowable

    def flowables(self):
        id = self.get('id')
        for i, flowable in enumerate(self.build_flowables()):
            if i == 0 and id:
                flowable.id = id
            yield flowable

    def build_flowables(self):
        yield self.build_flowable()

    def build_flowable(self):
        raise NotImplementedError('tag: %s' % self.tag_name)


class BodySubElement(BodyElementBase):
    def process(self):
        raise NotImplementedError('tag: %s' % self.tag_name)


class InlineElement(DocBookNode):
    style = None

    def styled_text(self, strip_leading_whitespace=False):
        return self.build_styled_text(strip_leading_whitespace)

    def build_styled_text(self, strip_leading_whitespace=False):
        return self.process_content(strip_leading_whitespace, style=self.style)


class GroupingElement(BodyElement):
    style = None
    grouped_flowables_class = StaticGroupedFlowables

    def build_flowables(self, **kwargs):
        yield self.grouped_flowables_class(self.children_flowables(),
                                           style=self.style, **kwargs)


from . import nodes

class DocBookReader(object):
    rngschema = None
    namespace = DocBookNode.NAMESPACE

    def parse(self, file):
        filename = getattr(file, 'name', None)
        parser = elementtree.Parser(DocBookNode, #namespace=self.namespace,
                                    schema=self.rngschema)
        xml_tree = parser.parse(filename)
        doctree = xml_tree.getroot()
        return self.from_doctree(doctree)

    def from_doctree(self, doctree):
        mapped_tree = DocBookNode.map_node(doctree)
        return mapped_tree.children_flowables()
