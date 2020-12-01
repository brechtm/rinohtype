# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from pathlib import Path

from docutils.core import publish_doctree
from docutils.io import FileInput
from docutils.parsers.rst import Parser as ReStructuredTextParser

from ...document import DocumentTree
from ...text import MixedStyledText

from .. import (TreeNode, TreeNodeMeta, InlineNode, BodyNode, BodySubNode,
                GroupingNode, DummyNode, Reader)


__all__ = ['DocutilsNode', 'DocutilsInlineNode',
           'DocutilsBodyNode', 'DocutilsBodySubNode',
           'DocutilsGroupingNode', 'DocutilsDummyNode',
           'ReStructuredTextReader', 'from_doctree']


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

    @staticmethod
    def node_location(node):
        return node.source, node.line, node.tagname

    @property
    def root(self):
        node = self.node
        while node.document is None:
            node = node.parent  # https://sourceforge.net/p/docutils/bugs/410/
        settings = node.document.settings
        try:                    # Sphinx
            sphinx_env = settings.env
        except AttributeError:  # plain docutils
            return Path(settings._source).parent
        return Path(sphinx_env.srcdir)

    @property
    def _ids(self):
        return self.get('ids')

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
            styled_text.classes.extend(self.get('classes'))
        except AttributeError:
            pass
        return styled_text


class DocutilsBodyNode(DocutilsNode, BodyNode):
    def flowables(self):
        classes = self.get('classes')
        for flowable in super().flowables():
            flowable.classes.extend(classes)
            yield flowable


class DocutilsBodySubNode(DocutilsNode, BodySubNode):
    pass


class DocutilsGroupingNode(DocutilsBodyNode, GroupingNode):
    pass


class DocutilsDummyNode(DocutilsNode, DummyNode):
    pass


from . import nodes


class DocutilsReader(Reader):
    parser_class = None

    def parse(self, filename_or_file, **context):
        try:
            file, filename = None, Path(filename_or_file)
            kwargs = dict(source_path=str(filename),
                          settings_overrides=dict(input_encoding='utf-8'))
        except TypeError:
            file, kwargs = filename_or_file, {}
        doctree = publish_doctree(file, source_class=FileInput,
                                  parser=self.parser_class(), **kwargs)
        return from_doctree(doctree, **context)


class ReStructuredTextReader(DocutilsReader):
    extensions = ('rst', )
    parser_class = ReStructuredTextParser


def from_doctree(doctree, **context):
    mapped_tree = DocutilsNode.map_node(doctree.document, **context)
    flowables = mapped_tree.children_flowables()
    return DocumentTree(flowables)
