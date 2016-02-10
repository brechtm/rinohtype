# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os
import re

from urllib.parse import urljoin
from urllib.request import pathname2url

from ...styleds import Paragraph
from ...text import MixedStyledText
from ...util import NotImplementedAttribute

from ... import DATA_PATH

from .. import (TreeNode, InlineNode, BodyNode, BodySubNode, GroupingNode,
                DummyNode, TreeNodeMeta)


__all__ = ['filter', 'strip_and_filter',
           'ElementTreeNode', 'ElementTreeInlineNode', 'ElementTreeBodyNode',
           'ElementTreeBodySubNode', 'ElementTreeGroupingNode',
           'ElementTreeDummyNode', 'ElementTreeNodeMeta']


CATALOG_PATH = os.path.join(DATA_PATH, 'xml', 'catalog')
CATALOG_URL = urljoin('file:', pathname2url(CATALOG_PATH))
CATALOG_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"


RE_WHITESPACE = re.compile('[\t\r\n ]+')


def filter(text, strip_leading_whitespace):
    if text:
        yield text, str(text).endswith(' ')


def strip_and_filter(text, strip_leading_whitespace):
    if not text:
        return
    if strip_leading_whitespace:
        text = text.lstrip()
    for item, strip_leading_whitespace in filter(text,
                                                 strip_leading_whitespace):
        yield item, strip_leading_whitespace


def filter_whitespace(text, children, strip_leading_ws):
    for item, strip_leading_ws in strip_and_filter(text, strip_leading_ws):
        yield item
    for child in children:
        child_text = child.styled_text(strip_leading_ws)
        for item, strip_leading_ws in filter(child_text, strip_leading_ws):
            yield item
        for item, strip_leading_ws in strip_and_filter(child.tail,
                                                       strip_leading_ws):
            yield item


def process_content(text, children, strip_leading_whitespace=True, style=None):
    text_items = filter_whitespace(text, children, strip_leading_whitespace)
    return MixedStyledText([item for item in text_items], style=style)


class ElementTreeNode(TreeNode):
    NAMESPACE = NotImplementedAttribute()

    @classmethod
    def strip_namespace(cls, tag):
        if '{' in tag:
            assert tag.startswith('{{{}}}'.format(cls.NAMESPACE))
            return tag[tag.find('}') + 1:]
        else:
            return tag

    @classmethod
    def node_tag_name(cls, node):
        return cls.strip_namespace(node.tag)

    @staticmethod
    def node_parent(node):
        return node._parent

    @staticmethod
    def node_children(node):
        return node.getchildren()

    @property
    def _id(self):
        return self.get('id')

    @property
    def _location(self):
        filename = self.node._root._roottree._filename
        return filename, self.node.sourceline, self.tag_name

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
        return process_content(self.text, self.getchildren(),
                               strip_leading_whitespace, style=style)


class ElementTreeInlineNode(ElementTreeNode, InlineNode):
    def styled_text(self, strip_leading_whitespace=False):
        return self.build_styled_text(strip_leading_whitespace)

    def build_styled_text(self, strip_leading_whitespace=False):
        return self.process_content(strip_leading_whitespace, style=self.style)


class ElementTreeBodyNode(ElementTreeNode, BodyNode):
    def flowables(self):
        classes = self.get('classes')
        for flowable in super().flowables():
            flowable.classes = classes
            yield flowable


class ElementTreeBodySubNode(ElementTreeNode, BodySubNode):
    pass


class ElementTreeGroupingNode(ElementTreeBodyNode, GroupingNode):
    def children_flowables(self):
        strip_leading_whitespace = True
        paragraph = []
        for item, strip_leading_whitespace \
                in strip_and_filter(self.text, strip_leading_whitespace):
            paragraph.append(item)
        for child in self.getchildren():
            try:
                child_text = child.styled_text(strip_leading_whitespace)
                for item, strip_leading_whitespace \
                        in filter(child_text, strip_leading_whitespace):
                    paragraph.append(child_text)
            except AttributeError:
                if paragraph and paragraph[0]:
                    yield Paragraph(paragraph)
                paragraph = []
                for flowable in child.flowables():
                    yield flowable
            for item, strip_leading_whitespace \
                    in strip_and_filter(child.tail, strip_leading_whitespace):
                paragraph.append(item)
        if paragraph and paragraph[0]:
            yield Paragraph(paragraph)


class ElementTreeDummyNode(ElementTreeNode, DummyNode):
    pass


class ElementTreeNodeMeta(TreeNodeMeta):
    root = ElementTreeNode
    bases = (ElementTreeInlineNode, ElementTreeBodyNode, ElementTreeBodySubNode,
             ElementTreeGroupingNode, ElementTreeDummyNode)
