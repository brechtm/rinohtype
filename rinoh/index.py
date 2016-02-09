# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .annotation import NamedDestination
from .flowable import GroupedFlowables, GroupedFlowablesStyle, DummyFlowable
from .paragraph import Paragraph
from .reference import Referenceable, Reference, PAGE
from .util import intersperse


__all__ = ['Index', 'IndexStyle', 'IndexTerm', 'SingleIndexTerm', 'IndexTarget']


class IndexStyle(GroupedFlowablesStyle):
    pass


class Index(GroupedFlowables):
    style_class = IndexStyle
    location = 'index'

    def __init__(self, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.source = self

    def flowables(self, container):
        document = container.document
        index_entries = container.document.index_entries
        entries = sorted(index_entries)
        for entry in entries:
            pages = intersperse((Reference(index_target.get_id(document), PAGE)
                                 for index_target in index_entries[entry]), ', ')
            yield Paragraph([entry.name, ', '] + list(pages))


class IndexTerm(object):
    def __init__(self, target, name, subentry_name=None):
        self.name = name
        self.subentry_name = subentry_name
        self.target = target

    @property
    def name_tuple(self):
        return self.name, self.subentry_name

    def __eq__(self, other):
        return self.name_tuple == other.name_tuple

    def __lt__(self, other):
        return self.name_tuple < other.name_tuple

    def __hash__(self):
        return hash(self.name_tuple)


class SingleIndexTerm(IndexTerm):
    def __init__(self, target, name, subentry_name=None):
        super().__init__(target, name, subentry_name)


class IndexTarget(DummyFlowable, Referenceable):
    category = 'Index'

    def __init__(self, index_term, parent=None):
        super().__init__(parent=parent)
        self.index_term = index_term

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        document = flowable_target.document
        document.index_entries.setdefault(self.index_term, []).append(self)

    def flow(self, container, last_descender, state=None):
        result = super().flow(container, last_descender, state=state)
        reference_id = self.get_id(container.document)
        destination = NamedDestination(str(reference_id))
        container.canvas.annotate(destination, 0, 0, container.width, None)
        self.update_page_reference(container.page)
        return result


