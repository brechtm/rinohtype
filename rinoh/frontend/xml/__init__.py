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

from ...text import MixedStyledText
from ...util import NotImplementedAttribute

from ... import DATA_PATH

from .. import (TreeNode, InlineNode, BodyNode, BodySubNode, GroupingNode,
                DummyNode)

__all__ = ['filter', 'strip_and_filter',
           'ElementTreeNode', 'ElementTreeInlineNode', 'ElementTreeBodyNode',
           'ElementTreeBodySubNode', 'ElementTreeGroupingNode',
           'ElementTreeDummyNode']


CATALOG_PATH = os.path.join(DATA_PATH, 'xml', 'catalog')
CATALOG_URL = urljoin('file:', pathname2url(CATALOG_PATH))
CATALOG_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"


RE_WHITESPACE = re.compile('[\t\r\n ]+')


def filter(text, strip_leading_whitespace):
    if text:
        yield text, str(text).endswith(' ')


def strip_and_filter(text, strip_leading_whitespace):
    if strip_leading_whitespace:
        text = text.lstrip()
    for item, strip_leading_whitespace in filter(text,
                                                 strip_leading_whitespace):
        yield item, strip_leading_whitespace


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
    pass


class ElementTreeDummyNode(ElementTreeNode, DummyNode):
    pass


def element_factory(xml_frontend):
    class CustomElement(xml_frontend.BaseElement):
        def process(self, *args, **kwargs):
            result = self.parse(*args, **kwargs)
            try:
                result.source = self
            except AttributeError:
                pass
            return result

        def parse(self, *args, **kwargs):
            raise NotImplementedError('tag: %s' % self.tag)

        @property
        def location(self):
            tag = self.tag.split('}', 1)[1] if '}' in self.tag else self.tag
            return '{}: <{}> at line {}'.format(self.filename, tag,
                                                self.sourceline)

    class NestedElement(CustomElement):
        def parse(self, *args, **kwargs):
            return self.process_content()

        def process_content(self):
            content = re.sub('[\t\r\n ]+', ' ', self.text)
            for child in self.getchildren():
                content += child.process() + child.tail
            return content

    return CustomElement, NestedElement
