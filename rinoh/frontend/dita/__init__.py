# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from ...util import all_subclasses

from ..docbook import (CustomElement, BodyElement, BodySubElement,
                       InlineElement, GroupingElement)
from ..xml import elementtree

from . import nodes

CustomElement.MAPPING = {cls.__name__.lower().replace('_', '-'): cls
                         for cls in all_subclasses(CustomElement)}


class DITAReader(object):
    def parse(self, file):
        filename = getattr(file, 'name', None)
        parser = elementtree.Parser(CustomElement)
        xml_tree = parser.parse(filename)
        doctree = xml_tree.getroot()
        return self.from_doctree(doctree)

    def from_doctree(self, doctree):
        mapped_tree = CustomElement.map_node(doctree)
        return mapped_tree.tree()
