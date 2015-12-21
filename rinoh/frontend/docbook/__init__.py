# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import re

from itertools import chain

from .. import TreeNode

from ..xml import elementtree

from ...flowable import StaticGroupedFlowables
from ...text import MixedStyledText


DOCBOOK_NS = 'http://docbook.org/ns/docbook'

RE_WHITESPACE = re.compile('[\t\r\n ]+')


def strip_namespace(tag):
    if '{' in tag:
        assert tag.startswith('{{{}}}'.format(DOCBOOK_NS))
        return tag[tag.find('}') + 1:]
    else:
        return tag


def filter(text, strip_leading_whitespace):
    if text:
        yield text, str(text).endswith(' ')


def strip_and_filter(text, strip_leading_whitespace):
    if strip_leading_whitespace:
        text = text.lstrip()
    for item, strip_leading_whitespace in filter(text,
                                                 strip_leading_whitespace):
        yield item, strip_leading_whitespace


class DocBookNode(TreeNode):
    @staticmethod
    def node_tag_name(node):
        return strip_namespace(node.tag)

    @staticmethod
    def node_parent(node):
        return node._parent

    @staticmethod
    def node_children(node):
        return node.getchildren()

    @property
    def _location(self):
        return self.node.filename, self.node.sourceline, self.tag_name

    @property
    def text(self):
        if self.node.text:
            if self.get('xml:space') == 'preserve':
                return self.node.text
            else:
                return RE_WHITESPACE.sub(' ', self.node.text)
        else:
            return ''

    @property
    def tail(self):
        if self.node.tail:
            return RE_WHITESPACE.sub(' ', self.node.tail)
        else:
            return None

    @property
    def attributes(self):
        return self.node.attrib

    def get(self, key, default=None):
        return self.node.get(key, default)

    def __getitem__(self, name):
        return self.node[name]

    def process_content(self, strip_leading_whitespace=True, style=None):
        text_items = self._filter_whitespace(strip_leading_whitespace)
        return MixedStyledText([item for item in text_items], style=style)

    def _filter_whitespace(self, strip_leading_ws):
        for item, strip_leading_ws in strip_and_filter(self.text,
                                                       strip_leading_ws):
            yield item
        for child in self.getchildren():
            child_text = child.styled_text(strip_leading_ws)
            for item, strip_leading_ws in filter(child_text, strip_leading_ws):
                yield item
            for item, strip_leading_ws in strip_and_filter(child.tail,
                                                           strip_leading_ws):
                yield item


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
    namespace = DOCBOOK_NS

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
