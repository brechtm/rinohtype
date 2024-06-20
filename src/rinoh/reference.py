# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import re
from itertools import chain, zip_longest

from .annotation import NamedDestinationLink
from .attribute import Attribute, Bool, OptionSet, OverrideDefault
from .flowable import (Flowable, LabeledFlowable, DummyFlowable,
                       LabeledFlowableStyle)
from .layout import ContainerOverflow
from .number import NumberStyle, Label, format_number
from .paragraph import Paragraph, ParagraphStyle, ParagraphBase
from .strings import StringField
from .style import HasClass, HasClasses, Styled
from .text import (StyledText, TextStyle, SingleStyledText,
                   MixedStyledTextBase, MixedStyledText, ErrorText)
from .util import NotImplementedAttribute

__all__ = ['Reference', 'ReferenceField', 'ReferenceText', 'ReferenceType',
           'ReferencingParagraph', 'ReferencingParagraphStyle',
           'Note', 'NoteMarkerBase', 'NoteMarkerByID', 'NoteMarkerWithNote',
           'NoteMarkerStyle', 'Field',
           'PAGE_NUMBER', 'NUMBER_OF_PAGES', 'SECTION_NUMBER',
           'SECTION_TITLE', 'DOCUMENT_TITLE', 'DOCUMENT_SUBTITLE']


class ReferenceType(OptionSet):
    values = 'reference', 'number', 'title', 'page', 'custom'


# examples for section "3.2 Some Title"
# reference: Section 3.2
# number:    3.2
# title:     Some Title
# page:      <number of the page on which section 3.2 starts>


class ReferenceStyle(TextStyle, NumberStyle):
    type = Attribute(ReferenceType, ReferenceType.REFERENCE,
                     'How the reference should be displayed')
    link = Attribute(Bool, True, 'Create a hyperlink to the reference target')
    quiet = Attribute(Bool, False, 'If the given reference type does not exist'
                                   'for the target, resolve to an empty string'
                                   'instead of making a fuss about it')


class ReferenceBase(MixedStyledTextBase):
    style_class = ReferenceStyle

    def __init__(self, type=None, custom_title=None, style=None, parent=None,
                 source=None):
        super().__init__(style=style, parent=parent, source=source)
        self.type = type
        self.custom_title = custom_title
        if custom_title:
            custom_title.parent = self

    def __str__(self):
        result = "'{{{}}}'".format((self.type or 'none').upper())
        if self.style is not None:
            result += ' ({})'.format(self.style)
        return result

    def copy(self, parent=None):
        return type(self)(self.type, self.custom_title, style=self.style,
                          parent=parent, source=self.source)

    def target_id(self, document):
        raise NotImplementedError

    def is_title_reference(self, container):
        reference_type = self.type or self.get_style('type', container)
        return reference_type == ReferenceType.TITLE

    def children(self, container, type=None):
        document = container.document
        type = type or self.type or self.get_style('type', container)
        if container is None:
            return '$REF({})'.format(type)
        target_id = self.target_id(document)
        if type == ReferenceType.CUSTOM:
            yield self.custom_title
            return
        try:
            text = document.get_reference(target_id, type)
        except KeyError:
            if self.custom_title:
                text = self.custom_title
            elif self.get_style('quiet', container):
                text = ''
            else:
                self.warn(f"Target '{target_id}' has no '{type}' reference",
                          container)
                text = ErrorText('??', parent=self)
        if type == ReferenceType.TITLE:  # prevent infinite recursion
            document.title_targets.update(self.referenceable_ids)
            if target_id in document.title_targets:
                self.warn("Circular 'title' reference replaced with "
                          "'reference' reference", container)
                yield from self.children(container, type='reference')
                return
            document.title_targets.add(target_id)
        yield (text.copy(parent=self) if isinstance(text, Styled)
               else SingleStyledText(text, parent=self))
        document.title_targets.clear()

    def get_annotation(self, container):
        assert self.annotation is None
        if self.get_style('link', container):
            target_id = self.target_id(container.document)
            return NamedDestinationLink(str(target_id))


class Reference(ReferenceBase):
    def __init__(self, target_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._target_id = target_id

    def copy(self, parent=None):
        return type(self)(self._target_id, self.type, self.custom_title,
                          style=self.style, parent=parent, source=self.source)

    def target_id(self, document):
        return self._target_id


class DirectReference(ReferenceBase):
    def __init__(self, referenceable, type='number', **kwargs):
        super().__init__(type=type, **kwargs)
        self.referenceable = referenceable

    def target_id(self, document):
        return self.referenceable.get_id(document)


class ReferenceField(ReferenceBase):
    def target_id(self, document):
        target_id_or_flowable = self.paragraph.target_id_or_flowable
        return (target_id_or_flowable.get_id(document)
                if isinstance(target_id_or_flowable, Flowable)
                else target_id_or_flowable)


class ReferenceText(StyledText):
    RE_TYPES = re.compile('{(' + '|'.join(ReferenceType.values) + ')}', re.I)

    @classmethod
    def check_type(cls, value):
        return isinstance(value, (str, type(None), StyledText))

    @classmethod
    def _substitute_variables(cls, text, style):
        return substitute_variables(text, cls.RE_TYPES, create_reference_field,
                                    super()._substitute_variables, style)


def create_reference_field(key, style=None):
    return ReferenceField(key.lower(), style=style)


class ReferencingParagraphStyle(ParagraphStyle):
    text = Attribute(ReferenceText, ReferenceField('title'),
                     'The text content of this paragraph')


class ReferencingParagraph(ParagraphBase):
    style_class = ReferencingParagraphStyle

    def __init__(self, target_id_or_flowable, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.target_id_or_flowable = target_id_or_flowable

    def text(self, container):
        return self.get_style('text', container).copy(parent=self)

    def _target_id(self, document):
        target_id_or_flowable = self.target_id_or_flowable
        return (target_id_or_flowable.get_id(document)
                if isinstance(target_id_or_flowable, Flowable)
                else target_id_or_flowable)

    def _target_flowable(self, document):
        return document.elements[self._target_id(document)]

    def target_style(self, document):
        """Filter selection on the ``style`` attribute of the target flowable"""
        return self._target_flowable(document).style

    def target_has_class(self, document):
        """Filter selection on a class of the target flowable"""
        return HasClass(self._target_flowable(document))

    def target_has_classes(self, document):
        """Filter selection on a set of classes of the target flowable"""
        return HasClasses(self._target_flowable(document))

    def target_is_of_type(self, document):
        """Filter selection on the type of the target flowable"""
        return IsOfType(self._target_flowable(document))


class IsOfType:
    def __init__(self, styled):
        self.styled = styled

    def __eq__(self, type_name):
        return type_name == type(self.styled).__name__


class NoteLocation(OptionSet):
    """Where a :class:`.Note` is placed"""

    values = 'in-place', 'footer'


class NoteStyle(LabeledFlowableStyle):
    location = Attribute(NoteLocation, 'footer', 'Where to place the note')


class Note(LabeledFlowable):
    category = 'note'
    style_class = NoteStyle

    def __init__(self, flowable, id=None, style=None, parent=None):
        label = Paragraph(DirectReference(self))
        super().__init__(label, flowable, id=id, style=style, parent=parent)

    def flow(self, container, last_descender, state=None, footnote=False,
             **kwargs):
        location = self.get_style('location', container)
        if not footnote and location == NoteLocation.FOOTER:
            return 0, 0, last_descender
        return super().flow(container, last_descender, state, **kwargs)


class NoteMarkerStyle(ReferenceStyle):
    type = OverrideDefault(ReferenceType.NUMBER)


class NoteMarkerBase(ReferenceBase, Label):
    style_class = NoteMarkerStyle

    def __init__(self, custom_label=None, **kwargs):
        super().__init__(**kwargs)
        Label.__init__(self, custom_label=custom_label)

    def prepare(self, flowable_target):
        document = flowable_target.document
        target_id = self.target_id(document)
        try:  # set reference only once (notes can be referenced multiple times)
            document.get_reference(target_id, 'number')
        except KeyError:
            if self.get_style('custom_label', flowable_target):
                assert self.custom_label is not None
                label = self.custom_label
            else:
                number_format = self.get_style('number_format', flowable_target)
                counter = document.counters.setdefault(Note.category, [])
                counter.append(self)
                label = format_number(len(counter), number_format)
            formatted_label = self.format_label(label, flowable_target)
            document.set_reference(target_id, 'number', formatted_label)

    def before_placing(self, container, preallocate=False):
        note = container.document.elements[self.target_id(container.document)]
        if note.get_style('location', container) == NoteLocation.FOOTER:
            if not container._footnote_space.add_footnote(note, preallocate):
                raise ContainerOverflow
        super().before_placing(container, preallocate)


class NoteMarkerByID(Reference, NoteMarkerBase):
    pass


class NoteMarkerWithNote(DirectReference, NoteMarkerBase):
    def prepare(self, flowable_target):
        self.referenceable.prepare(flowable_target)
        super().prepare(flowable_target)


class FieldTypeBase(object):
    name = NotImplementedAttribute()

    def __str__(self):
        return '{{{}}}'.format(self.key)

    @property
    def key(self):
        return self.name.upper().replace(' ', '_')


class FieldType(FieldTypeBase):
    all = {}

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.all[self.key] = self

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.name)

    @classmethod
    def from_string(cls, string):
        return cls.all[string.upper()]


PAGE_NUMBER = FieldType('page number')
NUMBER_OF_PAGES = FieldType('number of pages')
DOCUMENT_TITLE = FieldType('document title')
DOCUMENT_SUBTITLE = FieldType('document subtitle')
DOCUMENT_AUTHOR = FieldType('document author')


class SectionFieldTypeMeta(type):
    def __new__(metacls, classname, bases, cls_dict):
        cls = super().__new__(metacls, classname, bases, cls_dict)
        try:
            SectionFieldType.all[classname] = cls
        except NameError:
            pass
        return cls

    @property
    def key(cls):
        return cls.__name__


class SectionFieldType(FieldTypeBase, metaclass=SectionFieldTypeMeta):
    reference_type = None
    all = {}

    def __init__(self, level):
        super().__init__()
        self.level = level

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __str__(self):
        return '{{{key}({level})}}'.format(key=self.key, level=self.level)

    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.level)

    REGEX = re.compile(r'(?P<name>[a-z_]+)\((?P<level>\d+)\)', re.IGNORECASE)

    @classmethod
    def from_string(cls, string):
        m = cls.REGEX.match(string)
        section_field, level = m.group('name', 'level')
        return cls.all[section_field.upper()](int(level))


class SECTION_NUMBER(SectionFieldType):
    name = 'section number'
    reference_type = 'number'


class SECTION_TITLE(SectionFieldType):
    name = 'section title'
    reference_type = 'title'


RE_STRINGFIELD = r'[@$](?:[a-z_][a-z0-9_]*)'


class Field(MixedStyledTextBase):
    def __init__(self, type, id=None, style=None, parent=None, source=None):
        super().__init__(id=id, style=style, parent=parent, source=source)
        self.type = type

    def __str__(self):
        result = "'{}'".format(self.type)
        if self.style is not None:
            result += ' ({})'.format(self.style)
        return result

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, repr(self.type))

    @classmethod
    def parse_string(cls, string, style=None):
        try:
            field = FieldType.from_string(string)
        except KeyError:
            field = SectionFieldType.from_string(string)
        return cls(field, style=style)

    def copy(self, parent=None):
        return type(self)(self.type, style=self.style, parent=parent,
                          source=self.source)

    def children(self, container):
        if container is None:
            text = '${}'.format(self.type)
        elif self.type == PAGE_NUMBER:
            text = container.page.formatted_number
        elif self.type == NUMBER_OF_PAGES:
            part = container.document_part
            text = format_number(part.number_of_pages, part.page_number_format)
        elif self.type == DOCUMENT_TITLE:
            text = container.document.get_metadata('title')
        elif self.type == DOCUMENT_SUBTITLE:
            text = container.document.get_metadata('subtitle')
        elif self.type == DOCUMENT_AUTHOR:
            text = container.document.get_metadata('author')
        elif isinstance(self.type, SectionFieldType):
            doc = container.document
            section = container.page.get_current_section(self.type.level)
            section_id = section.get_id(doc) if section else None
            if section_id:
                text = doc.get_reference(section_id, self.type.reference_type,
                                         '\N{ZERO WIDTH SPACE}')
            else:
                text = '\N{ZERO WIDTH SPACE}'
        else:
            text = '?'
        if text is None:
            return
        elif isinstance(text, Styled):
            yield text.copy(parent=self)
        else:
            yield SingleStyledText(text, parent=self)

    RE_FIELD = re.compile('{(' + '|'.join(chain(FieldType.all,
                                                (r'{}\(\d+\)'.format(name)
                                                 for name
                                                 in SectionFieldType.all)))
                          + '|' + RE_STRINGFIELD
                          + ')}', re.IGNORECASE)

    @classmethod
    def substitute(cls, text, substitute_others, style):
        def create_variable(key, style=None):
            try:
                return cls.parse_string(key.lower(), style=style)
            except AttributeError:
                return StringField.parse_string(key, style=style)

        return substitute_variables(text, cls.RE_FIELD, create_variable,
                                    substitute_others, style)


def substitute_variables(text, split_regex, create_variable,
                         substitute_others, style):
    def sub(parts):
        iter_parts = iter(parts)
        for other_text, variable_type in zip_longest(iter_parts, iter_parts):
            if other_text:
                yield substitute_others(other_text, style=None)
            if variable_type:
                yield create_variable(variable_type)

    parts = split_regex.split(text)
    if len(parts) == 1:                             # no variables
        return substitute_others(text, style=style)
    elif sum(1 for part in parts if part) == 1:     # only a single variable
        variable_type, = (part for part in parts if part)
        return create_variable(variable_type, style=style)
    else:                                           # variable(s) and text
        return MixedStyledText(sub(parts), style=style)
