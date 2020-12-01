# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import re

from copy import copy
from itertools import chain, zip_longest

from .annotation import NamedDestinationLink, AnnotatedSpan
from .attribute import Attribute, OptionSet
from .flowable import Flowable, LabeledFlowable, DummyFlowable
from .layout import ReflowRequired, ContainerOverflow
from .number import NumberStyle, Label, format_number
from .paragraph import Paragraph, ParagraphStyle, ParagraphBase
from .strings import StringCollection, StringField
from .style import HasClass, HasClasses
from .text import (SingleStyledTextBase, MixedStyledTextBase, TextStyle,
                   StyledText, SingleStyledText, MixedStyledText)
from .util import NotImplementedAttribute


__all__ = ['Reference', 'ReferenceField', 'ReferenceText', 'ReferenceType',
           'ReferencingParagraph', 'ReferencingParagraphStyle',
           'Note', 'RegisterNote', 'NoteMarkerBase', 'NoteMarkerByID',
           'NoteMarkerWithNote', 'NoteMarkerStyle',
           'Field', 'PAGE_NUMBER', 'NUMBER_OF_PAGES', 'SECTION_NUMBER',
           'SECTION_TITLE', 'DOCUMENT_TITLE', 'DOCUMENT_SUBTITLE']


class ReferenceType(OptionSet):
    values = 'reference', 'number', 'title', 'page'


# examples for section "3.2 Some Title"
# reference: Section 3.2
# number:    3.2
# title:     Some Title
# page:      <number of the page on which section 3.2 starts>


class ReferenceBase(MixedStyledTextBase):
    def __init__(self, type='number', link=True, quiet=False, style=None,
                 parent=None, source=None):
        super().__init__(style=style, parent=parent, source=source)
        self.type = type
        self.link = link
        self.quiet = quiet

    def __str__(self):
        result = "'{{{}}}'".format(self.type.upper())
        if self.style is not None:
            result += ' ({})'.format(self.style)
        return result

    def copy(self, parent=None):
        return type(self)(self.type, self.link, self.quiet,
                          style=self.style, parent=parent)

    def target_id(self, document):
        raise NotImplementedError

    def children(self, container):
        if container is None:
            return '$REF({})'.format(self.type)
        target_id = self.target_id(container.document)
        try:
            if self.type == ReferenceType.REFERENCE:
                category = container.document.elements[target_id].category
                number = container.document.get_reference(target_id, 'number')
                text = '{}\N{No-BREAK SPACE}{}'.format(category, number)
            elif self.type == ReferenceType.NUMBER:
                text = container.document.get_reference(target_id, self.type)
                if text is None:
                    if not self.quiet:
                        self.warn('Cannot reference "{}"'.format(target_id),
                                  container)
                    text = ''
            elif self.type == ReferenceType.PAGE:
                try:
                    text = str(container.document.page_references[target_id])
                except KeyError:
                    text = '??'
            elif self.type == ReferenceType.TITLE:
                text = container.document.get_reference(target_id, self.type)
            else:
                raise NotImplementedError(self.type)
        except KeyError:
            self.warn("Unknown label '{}'".format(target_id), container)
            text = "??".format(target_id)
        # TODO: clean up
        if isinstance(text, MixedStyledTextBase):
            for child in text.children(container):
                child_copy = copy(child)
                child_copy.parent = self
                yield child_copy
        elif isinstance(text, SingleStyledTextBase):
            yield text
        else:
            yield SingleStyledText(text, parent=self)

    def spans(self, container):
        spans = super().spans(container)
        if self.link:
            target_id = self.target_id(container.document)
            annotation = NamedDestinationLink(str(target_id))
            spans = (AnnotatedSpan(span, annotation) for span in spans)
        return spans


class Reference(ReferenceBase):
    def __init__(self, target_id, type='number', link=True, style=None,
                 quiet=False, **kwargs):
        super().__init__(type=type, link=link, style=style, quiet=quiet,
                         **kwargs)
        self._target_id = target_id

    def target_id(self, document):
        return self._target_id


class DirectReference(ReferenceBase):
    def __init__(self, referenceable, type='number', link=False, style=None,
                 **kwargs):
        super().__init__(type=type, link=link, style=style, **kwargs)
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


class Note(LabeledFlowable):
    category = 'Note'

    def __init__(self, flowable, id=None, style=None, parent=None):
        label = Paragraph(DirectReference(self))
        super().__init__(label, flowable, id=id, style=style, parent=parent)


class RegisterNote(DummyFlowable):
    def __init__(self, note, parent=None):
        super().__init__(parent=parent)
        self.note = note

    def prepare(self, flowable_target):
        self.note.prepare(flowable_target)


class NoteMarkerStyle(TextStyle, NumberStyle):
    pass


class NoteMarkerBase(ReferenceBase, Label):
    style_class = NoteMarkerStyle

    def __init__(self, custom_label=None, **kwargs):
        kwargs.update(type='number', link=True)
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

    def before_placing(self, container):
        note = container.document.elements[self.target_id(container.document)]
        if not container._footnote_space.add_footnote(note):
            raise ContainerOverflow
        super().before_placing(container)


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


from . import structure    # fills StringCollection.subclasses

RE_STRINGFIELD = ('|'.join(r'{}\.(?:[a-z_][a-z0-9_]*)'
                           .format(collection_name)
                           for collection_name in StringCollection.subclasses))


class Field(MixedStyledTextBase):
    def __init__(self, type, style=None):
        super().__init__(style=style)
        self.type = type

    def __str__(self):
        result = "'{}'".format(self.type)
        if self.style is not None:
            result += ' ({})'.format(self.style)
        return result

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, self.type)

    @classmethod
    def parse_string(cls, string, style=None):
        try:
            field = FieldType.from_string(string)
        except KeyError:
            field = SectionFieldType.from_string(string)
        return cls(field, style=style)

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
                text = (doc.get_reference(section_id, self.type.reference_type)\
                        or '\N{ZERO WIDTH SPACE}')
            else:
                text = '\N{ZERO WIDTH SPACE}'
        else:
            text = '?'
        if text is None:
            return
        elif isinstance(text, StyledText):
            text.parent = self
            yield text
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
