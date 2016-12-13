# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .attribute import Attribute, Bool
from .flowable import GroupedFlowables, GroupedFlowablesStyle, DummyFlowable
from .paragraph import Paragraph
from .reference import Reference
from .strings import StringField
from .structure import Section, Heading, SectionTitles
from .style import Styled
from .text import MixedStyledText, StyledText
from .util import intersperse


__all__ = ['IndexSection', 'Index', 'IndexStyle', 'IndexLabel', 'IndexTerm',
           'InlineIndexTarget', 'IndexTarget']


class IndexSection(Section):
    def __init__(self, title=None, flowables=None, style=None):
        section_title = title or StringField(SectionTitles, 'index')
        contents = [Heading(section_title, style='unnumbered')]
        if flowables:
            contents += list(flowables)
        else:
            contents.append(Index())
        super().__init__(contents, style=style)


class IndexStyle(GroupedFlowablesStyle):
    initials = Attribute(Bool, True, 'Group index entries based on their '
                                     'first letter')


class Index(GroupedFlowables):
    style_class = IndexStyle
    location = 'index'

    def __init__(self, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.source = self

    def flowables(self, container):
        initials = self.get_style('initials', container)
        def hande_level(index_entries, level=1):
            top_level = level == 1
            entries = sorted((name for name in index_entries if name),
                             key=lambda s: (s.lower(), s))
            last_section = None
            for entry in entries:
                first = entry[0]
                section = first.upper() if first.isalpha() else 'Symbols'
                term, subentries = index_entries[entry]
                if initials and top_level and section != last_section:
                    yield IndexLabel(section)
                    last_section = section
                target_ids = [target.get_id(document)
                              for term, target in subentries.get(None, ())]
                yield IndexEntry(term, level, target_ids)
                for paragraph in hande_level(subentries, level=level + 1):
                    yield paragraph

        document = container.document
        index_entries = container.document.index_entries
        for paragraph in hande_level(index_entries):
            yield paragraph


class IndexLabel(Paragraph):
    pass


class IndexEntry(Paragraph):
    def __init__(self, text_or_items, level, target_ids=None,
                 id=None, style=None, parent=None):
        if target_ids:
            refs = intersperse((Reference(id, 'page')
                                for id in target_ids), ', ')
            entry_text = text_or_items + ', ' + MixedStyledText(refs)
        else:
            entry_text = text_or_items
        super().__init__(entry_text, id=id, style=style, parent=parent)
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
                term_str = (term.to_string(flowable_target)
                            if isinstance(term, StyledText) else term)
                _, level_entries = level_entries.setdefault(term_str,
                                                            (term, {}))
            level_entries.setdefault(None, []).append((index_term, self))


class InlineIndexTarget(IndexTargetBase, StyledText):
    def to_string(self, flowable_target):
        return ''

    def spans(self, container):
        self.create_destination(container)
        return iter([])


class IndexTarget(IndexTargetBase, DummyFlowable):
    category = 'Index'

    def __init__(self, index_terms, parent=None):
        super().__init__(index_terms, parent=parent)

    def flow(self, container, last_descender, state=None, **kwargs):
        self.create_destination(container)
        return super().flow(container, last_descender, state=state)
