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
from .style import Styled
from .text import SingleStyledText, MixedStyledText, StyledText
from .util import intersperse


__all__ = ['Index', 'IndexStyle', 'IndexTerm',
           'InlineIndexTarget', 'IndexTarget']


class IndexStyle(GroupedFlowablesStyle):
    pass


class Index(GroupedFlowables):
    style_class = IndexStyle
    location = 'index'

    def __init__(self, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.source = self

    def flowables(self, container):
        def hande_level(index_entries, level=1):
            entries = sorted((name for name in index_entries if name),
                             key=lambda s: str(s).lower())
            for entry in entries:
                subentries = index_entries[entry]
                try:
                    refs = intersperse((Reference(tgt.get_id(document), PAGE)
                                       for term, tgt in subentries[None]), ', ')
                    entry_line = entry + ', ' + MixedStyledText(refs)
                except KeyError:
                    entry_line = entry
                yield IndexEntry(entry_line, level, style='index entry')
                for paragraph in hande_level(subentries, level=level + 1):
                    yield paragraph

        document = container.document
        index_entries = container.document.index_entries
        for paragraph in hande_level(index_entries):
            yield paragraph


class IndexEntry(Paragraph):
    def __init__(self, text_or_items, level, id=None, style=None, parent=None):
        super().__init__(text_or_items, id=id, style=style, parent=parent)
        self.index_level = level


class IndexTerm(tuple):
    def __new__(cls, *levels):
        return super().__new__(cls, levels)

    def __repr__(self):
        return type(self).__name__ + super().__repr__()


class IndexTargetBase(Styled):
    def __init__(self, index_terms, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_terms = index_terms

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        index_entries = flowable_target.document.index_entries
        for index_term in self.index_terms:
            level_entries = index_entries
            for term in index_term:
                level_entries = level_entries.setdefault(term, {})
            level_entries.setdefault(None, []).append((index_term, self))


class InlineIndexTarget(IndexTargetBase, StyledText):
    def spans(self, container):
        id = self.get_id(container.document)
        container.canvas.annotate(NamedDestination(str(id)), 0,
                                  container.cursor, container.width, None)
        document, page = container.document, container.page
        document.page_references[id] = page.number
        return iter([])


class IndexTarget(IndexTargetBase, DummyFlowable, Referenceable):
    category = 'Index'

    def __init__(self, index_terms, parent=None):
        super().__init__(index_terms, parent=parent)

    def flow(self, container, last_descender, state=None):
        self.create_destination(container, container.cursor)
        self.update_page_reference(container.page)
        return super().flow(container, last_descender, state=state)
