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
from .structure import Section, Heading
from .style import Styled
from .text import MixedStyledText, StyledText
from .util import intersperse


__all__ = ['IndexSection', 'Index', 'IndexStyle', 'IndexLabel', 'IndexSee',
           'IndexSeeAlso', 'IndexTerm', 'InlineIndexTarget', 'IndexTarget']


class IndexSection(Section):
    def __init__(self, title=None, flowables=None, style=None):
        section_title = title or StringField('index')
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
        def handle_level(index_entries, level=1):
            top_level = level == 1
            entries = sorted((name for name in index_entries if name),
                             key=lambda s: (s.lower(), s))
            last_section = None
            for entry in entries:
                term, entry_data = index_entries[entry]
                first = term[0]
                section = first.upper() if first.isalpha() else 'Symbols'
                if initials and top_level and section != last_section:
                    yield IndexLabel(section)
                    last_section = section
                target_ids = [target.get_id(document)
                              for term, target in entry_data['targets']]
                see_references = [('index_see', reference) for reference
                                  in entry_data['sees']]
                seealso_references = [('index_seealso', reference)
                                      for reference
                                      in entry_data['see_alsoes']]
                yield IndexEntry(term, level, target_ids,
                                 see_references + seealso_references)
                for paragraph in handle_level(entry_data['subentries'],
                                              level=level + 1):
                    yield paragraph

        document = container.document
        index_entries = container.document.index_entries
        for paragraph in handle_level(index_entries):
            yield paragraph


class IndexLabel(Paragraph):
    pass


class IndexEntry(Paragraph):
    def __init__(self, content, level, target_ids=None, see_references=(),
                 id=None, style=None, parent=None):
        if target_ids:
            refs = intersperse((Reference(id, 'page')
                                for id in target_ids), ', ')
            entry_text = content + ', ' + MixedStyledText(refs)
        else:
            entry_text = content
        if see_references:
            refs = intersperse((MixedStyledText((StringField(see_label), ' ',
                                                reference))
                                for see_label, reference in see_references),
                               '; ')
            entry_text = entry_text + ', ' + MixedStyledText(refs)
        super().__init__(entry_text, id=id, style=style, parent=parent)
        self.index_level = level


class IndexTerm(tuple):
    def __new__(cls, *levels):
        return super().__new__(cls, levels)

    def __repr__(self):
        return type(self).__name__ + super().__repr__()


class IndexSee(tuple):
    def __new__(cls, term, reference):
        return super().__new__(cls, (term, reference))

    def __repr__(self):
        return type(self).__name__ + super().__repr__()


class IndexSeeAlso(tuple):
    def __new__(cls, term, reference):
        return super().__new__(cls, (term, reference))

    def __repr__(self):
        return type(self).__name__ + super().__repr__()


def _index_node():
    """Create an empty node in the index term tree

    A node stores the page references, the see and see-also references and
    the subentries of a single (sub)term. Keeping these in dedicated fields
    keeps the tree keys free to hold actual index terms.
    """
    return {'targets': [], 'subentries': {}, 'sees': [], 'see_alsoes': []}


def _entry_node(entries, term):
    """Return the node for `term` in `entries`, creating it if necessary"""
    return entries.setdefault(term, (term, _index_node()))[1]


class IndexTargetBase(Styled):
    def __init__(self, index_terms, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index_terms = index_terms

    def prepare(self, flowable_target):
        super().prepare(flowable_target)
        index_entries = flowable_target.document.index_entries
        for index_term in self.index_terms:
            if isinstance(index_term, (IndexSee, IndexSeeAlso)):
                term, reference = index_term
                entry_data = _entry_node(index_entries, term)
                if isinstance(index_term, IndexSee):
                    entry_data['sees'].append(reference)
                else:
                    entry_data['see_alsoes'].append(reference)
                continue
            level_entries = index_entries
            for term in index_term:
                term_str = (term.to_string(flowable_target)
                            if isinstance(term, StyledText) else term)
                entry_data = _entry_node(level_entries, term_str)
                level_entries = entry_data['subentries']
            entry_data['targets'].append((index_term, self))


class InlineIndexTarget(IndexTargetBase, StyledText):
    def to_string(self, flowable_target):
        return ''

    def copy(self, parent=None):
        return MixedStyledText([])

    def spans(self, container):
        self.create_destination(container)
        return iter([])


class IndexTarget(IndexTargetBase, DummyFlowable):
    category = 'index'

    def __init__(self, index_terms, parent=None):
        super().__init__(index_terms, parent=parent)

    def flow(self, container, last_descender, state=None, **kwargs):
        self.create_destination(container)
        return super().flow(container, last_descender, state=state)
