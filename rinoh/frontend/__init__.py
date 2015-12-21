# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from rinoh.text import MixedStyledText


__all__ = ['TreeNode']


class TreeNodeMeta(type):
    def __new__(metaclass, name, bases, namespace):
        cls = super().__new__(metaclass, name, bases, namespace)
        node_name = cls.node_name or name.lower()
        if name not in __all__:
            TreeNode.MAPPING[node_name] = cls
        return cls


class TreeNode(object, metaclass=TreeNodeMeta):
    node_name = None

    MAPPING = {}

    @classmethod
    def map_node(cls, node):
        return cls.MAPPING[cls.node_tag_name(node)](node)

    def __init__(self, doctree_node):
        self.node = doctree_node

    def __getattr__(self, name):
        for child in self.getchildren():
            if child.tag_name == name:
                return child
        raise AttributeError('No such element: {}'.format(name))

    def __iter__(self):
        try:
            for child in self.parent.getchildren():
                if child.tag_name == self.tag_name:
                    yield child
        except AttributeError:
            # this is the root element
            yield self

    @property
    def tag_name(self):
        return self.node_tag_name(self.node)

    @property
    def parent(self):
        node_parent = self.node_parent(self.node)
        if node_parent is not None:
            return self.map_node(node_parent)

    def getchildren(self):
        return [self.map_node(child) for child in self.node_children(self.node)]

    def process_content(self, style=None):
        preserve_space = self.get('xml:space', None) == 'preserve'
        return MixedStyledText([text
                                for text in (child.styled_text(preserve_space)
                                             for child in self.getchildren())
                                if text], style=style)

    @property
    def location(self):
        source_file, line, tag_name = self._location
        return '{}:{} <{}>'.format(source_file, line, tag_name)

    @staticmethod
    def node_tag_name(node):
        raise NotImplementedError

    @staticmethod
    def node_parent(node):
        raise NotImplementedError

    @staticmethod
    def node_children(node):
        raise NotImplementedError

    @property
    def _location(self):
        raise NotImplementedError

    @property
    def text(self):
        raise NotImplementedError

    @property
    def attributes(self):
        return NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def __getitem__(self, name):
        raise NotImplementedError

