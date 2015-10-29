# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import re

from itertools import chain

from ..xml import elementtree

from ...flowable import StaticGroupedFlowables
from ...util import all_subclasses
from ...text import MixedStyledText


RE_WHITESPACE = re.compile('[\t\r\n ]+')


def strip_namespace(tag):
    return tag[tag.find('}') + 1:]


class CustomElement(object):
    @classmethod
    def map_node(cls, node):
        tag_without_ns = strip_namespace(node.tag)
        return cls.MAPPING[tag_without_ns](node)

    def __init__(self, doctree_node):
        self.node = doctree_node

    def __getattr__(self, name):
        for child in self.node.getchildren():
            if strip_namespace(child.tag) == name:
                return self.map_node(child)
        raise AttributeError('No such element: {}'.format(name))

    def __getitem__(self, name):
        return self.node[name]

    def __iter__(self):
        try:
            for child in self.parent.node.getchildren():
                if docbook_tag(child.tag) == docbook_tag(self.node.tag):
                    yield self.map_node(child)
        except AttributeError:
            # this is the root element
            yield self

    @property
    def attributes(self):
        return self.node.attrib

    @property
    def parent(self):
        if self.node._parent is not None:
            return self.map_node(self.node._parent)

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

    def get(self, key, default=None):
        return self.node.get(key, default)

    def getchildren(self):
        return [self.map_node(child) for child in self.node.getchildren()]

    def process_content(self, strip_leading_whitespace=True, style=None):
        text_items = self._filter_whitespace(strip_leading_whitespace)
        return MixedStyledText([item for item in text_items], style=style)

    def _filter_whitespace(self, strip_leading_whitespace):
        def filter(text):
            nonlocal strip_leading_whitespace
            if text:
                yield text
                strip_leading_whitespace = str(text).endswith(' ')

        def strip_and_filter(text):
            nonlocal strip_leading_whitespace
            if strip_leading_whitespace:
                text = text.lstrip()
            for item in filter(text):
                yield item

        for item in strip_and_filter(self.text):
            yield item
        for child in self.getchildren():
            child_text = child.styled_text(strip_leading_whitespace)
            for item in filter(child_text):
                yield item
            for item in strip_and_filter(child.tail):
                yield item

    @property
    def tag_name(self):
        return self.node.tag.split('}', 1)[-1]

    @property
    def location(self):
        return '{}: <{}> at line {}'.format(self.filename, self.tag_name,
                                            self.sourceline)



class BodyElementBase(CustomElement):
    def children_flowables(self, skip_first=0):
        children = self.getchildren()[skip_first:]
        return list(chain(*(item.flowables() for item in children)))


class BodyElement(BodyElementBase):
    def flowable(self):
        flowable, = self.flowables()
        return flowable

    def flowables(self):
        for flowable in self.build_flowables():
            yield flowable

    def build_flowables(self):
        yield self.build_flowable()

    def build_flowable(self):
        raise NotImplementedError('tag: %s' % self.tag_name)


class BodySubElement(BodyElementBase):
    def process(self):
        raise NotImplementedError('tag: %s' % self.tag_name)


class InlineElement(CustomElement):
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


DOCBOOK_NS = 'http://docbook.org/ns/docbook'

def docbook_tag(tag_name):
    return '{{{}}}'.format(DOCBOOK_NS) + tag_name


from . import nodes

CustomElement.MAPPING = {cls.__name__.lower(): cls
                         for cls in all_subclasses(CustomElement)}



class DocBookReader(object):
    rngschema = None
    namespace = DOCBOOK_NS

    def parse(self, file):
        filename = getattr(file, 'name', None)
        parser = elementtree.Parser(CustomElement, #namespace=self.namespace,
                                    schema=self.rngschema)
        xml_tree = parser.parse(filename)
        doctree = xml_tree.getroot()
        return self.from_doctree(doctree)

    def from_doctree(self, doctree):
        mapped_tree = CustomElement.map_node(doctree)
        return mapped_tree.children_flowables()
