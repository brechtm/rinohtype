# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import re

from .annotation import NamedDestinationLink, AnnotatedSpan
from .attribute import Attribute, OptionSet
from .flowable import Flowable, LabeledFlowable, DummyFlowable
from .layout import ReflowRequired
from .number import NumberStyle, Label, format_number
from .paragraph import Paragraph, ParagraphStyle, ParagraphBase
from .text import (SingleStyledTextBase, MixedStyledTextBase, TextStyle,
                   StyledText, MixedStyledText)


__all__ = ['Variable', 'Reference', 'ReferenceField', 'ReferenceText',
           'ReferenceType', 'ReferencingParagraph', 'ReferencingParagraphStyle',
           'Note', 'RegisterNote', 'NoteMarkerBase', 'NoteMarkerByID',
           'NoteMarkerWithNote',
           'PAGE_NUMBER', 'NUMBER_OF_PAGES', 'SECTION_NUMBER', 'SECTION_TITLE',
           'DOCUMENT_TITLE', 'DOCUMENT_SUBTITLE']


                            # examples for section "3.2 Some Title"
REFERENCE = 'reference'     # Section 3.2
NUMBER = 'number'           # 3.2
TITLE = 'title'             # Some Title
PAGE = 'page'               # <number of the page on which section 3.2 starts>


class ReferenceType(OptionSet):
    values = REFERENCE, NUMBER, TITLE, PAGE


class ReferenceBase(SingleStyledTextBase):
    def __init__(self, type=NUMBER, link=True, quiet=False,
                 style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.type = type
        self.link = link
        self.quiet = quiet

    def target_id(self, document):
        raise NotImplementedError

    def text(self, container):
        if container is None:
            return '$REF({})'.format(self.type)
        target_id = self.target_id(container.document)
        try:
            if self.type == REFERENCE:
                category = container.document.elements[target_id].category
                number = container.document.get_reference(target_id, NUMBER)
                text = '{}\N{No-BREAK SPACE}{}'.format(category, number)
            elif self.type == NUMBER:
                text = container.document.get_reference(target_id, self.type)
                if text is None:
                    if not self.quiet:
                        self.warn('Cannot reference "{}"'.format(target_id),
                                  container)
                    text = ''
            elif self.type == PAGE:
                try:
                    text = str(container.document.page_references[target_id])
                except KeyError:
                    text = '??'
            elif self.type == TITLE:
                text = container.document.get_reference(target_id, self.type)
            else:
                raise NotImplementedError(self.type)
        except KeyError:
            self.warn("Unknown label '{}'".format(target_id), container)
            text = "??".format(target_id)
        return text

    def spans(self, container):
        spans = super().spans(container)
        if self.link:
            target_id = self.target_id(container.document)
            annotation = NamedDestinationLink(str(target_id))
            spans = (AnnotatedSpan(span, annotation) for span in spans)
        return spans


class Reference(ReferenceBase):
    def __init__(self, target_id, type=NUMBER, link=True, style=None,
                 quiet=False, **kwargs):
        super().__init__(type=type, link=link, style=style, quiet=quiet,
                         **kwargs)
        self._target_id = target_id

    def target_id(self, document):
        return self._target_id


class DirectReference(ReferenceBase):
    def __init__(self, referenceable, type=NUMBER, link=False, style=None,
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
    RE_TYPES = re.compile('({(?:' + '|'.join(ReferenceType.values) + ')})',
                          re.IGNORECASE)

    @classmethod
    def check_type(cls, value):
        return isinstance(value, (str, type(None), StyledText))

    @classmethod
    def _substitute_variables(cls, text, style):
        items = []
        for part in (prt for prt in cls.RE_TYPES.split(text) if prt):
            if part.lower() in ('{' + ref_type + '}'
                                for ref_type in ReferenceType.values):
                field_type = part[1:-1].lower()
                item = ReferenceField(field_type)
            else:
                item = super()._substitute_variables(part, style=None)
            items.append(item)
        return MixedStyledText(items, style=style)


class ReferencingParagraphStyle(ParagraphStyle):
    text = Attribute(ReferenceText, ReferenceField(TITLE), 'The text content '
                                                           'of this paragraph')


class ReferencingParagraph(ParagraphBase):
    style_class = ReferencingParagraphStyle

    def __init__(self, target_id_or_flowable, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.target_id_or_flowable = target_id_or_flowable

    def text(self, container):
        return MixedStyledText(self.get_style('text', container), parent=self)



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
        kwargs.update(type=NUMBER, link=True)
        super().__init__(**kwargs)
        Label.__init__(self, custom_label=custom_label)

    def prepare(self, flowable_target):
        document = flowable_target.document
        target_id = self.target_id(document)
        try:  # set reference only once (notes can be referenced multiple times)
            document.get_reference(target_id, NUMBER)
        except KeyError:
            if self.get_style('custom_label', flowable_target):
                assert self.custom_label is not None
                formatted_number = str(self.custom_label)
            else:
                number_format = self.get_style('number_format', flowable_target)
                counter = document.counters.setdefault(Note.category, [])
                counter.append(self)
                formatted_number = format_number(len(counter), number_format)
            label = self.format_label(str(formatted_number), flowable_target)
            document.set_reference(target_id, NUMBER, str(label))

    def before_placing(self, container):
        note = container.document.elements[self.target_id(container.document)]
        try:
            container._footnote_space.add_footnote(note)
        except ReflowRequired:
            pass


class NoteMarkerByID(Reference, NoteMarkerBase):
    pass


class NoteMarkerWithNote(DirectReference, NoteMarkerBase):
    def prepare(self, flowable_target):
        self.referenceable.prepare(flowable_target)
        super().prepare(flowable_target)


class FieldType(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.name)

    def __str__(self):
        return self.name.upper().replace(' ', '_')


PAGE_NUMBER = FieldType('page number')
NUMBER_OF_PAGES = FieldType('number of pages')
DOCUMENT_TITLE = FieldType('document title')
DOCUMENT_SUBTITLE = FieldType('document subtitle')


class SectionFieldType(FieldType):
    ref_type = None

    def __init__(self, name, level):
        super().__init__(name)
        self.level = level

    def __repr__(self):
        return "{}('{}', {})".format(self.__class__.__name__, self.name,
                                     self.level)

    def __str__(self):
        return '{}({})'.format(super().__str__(), self.level)


class SECTION_NUMBER(SectionFieldType):
    ref_type = NUMBER

    def __init__(self, level):
        super().__init__('section number', level)


class SECTION_TITLE(SectionFieldType):
    ref_type = TITLE

    def __init__(self, level):
        super().__init__('section title', level)


class Variable(MixedStyledTextBase):
    def __init__(self, type, style=None):
        super().__init__(style=style)
        self.type = type

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, self.type)

    def text(self, container, **kwargs):
        if container is None:
            text = '${}'.format(self.type)
        elif self.type == PAGE_NUMBER:
            text = container.page.formatted_number
        elif self.type == NUMBER_OF_PAGES:
            document_section = container.document_part.document_section
            number = document_section.previous_number_of_pages
            text = format_number(number, container.page.number_format)
        elif self.type == DOCUMENT_TITLE:
            text = container.document.metadata['title']
        elif self.type == DOCUMENT_SUBTITLE:
            text = container.document.metadata['subtitle']
        elif isinstance(self.type, SectionFieldType):
            doc = container.document
            section = container.page.get_current_section(self.type.level)
            section_id = section.get_id(doc) if section else None
            if section_id:
                text = doc.get_reference(section_id, self.type.ref_type) or ''
            else:
                text = ''
        else:
            text = '?'
        return MixedStyledText(text, parent=self)
