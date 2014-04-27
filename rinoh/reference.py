# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .flowable import LabeledFlowable, DummyFlowable
from .number import NumberStyle, format_number
from .paragraph import Paragraph
from .style import PARENT_STYLE
from .text import StyledText, SingleStyledText, TextStyle


__all__ = ['FieldException', 'Referenceable',
           'Field', 'Variable', 'Reference', 'NoteMarker', 'Note',
           'RegisterNote', 'NoteMarkerWithNote',
           'PAGE_NUMBER', 'NUMBER_OF_PAGES', 'SECTION_NUMBER', 'SECTION_TITLE']


class FieldException(Exception):
    def __init__(self, field_spans):
        self.field_spans = field_spans


class Field(StyledText):
    def spans(self):
        yield self

    def split(self):
        yield

    @property
    def font(self):
        raise FieldException(self.field_spans)

    def field_spans(self, container):
        raise NotImplementedError


PAGE_NUMBER = 'page number'
NUMBER_OF_PAGES = 'number of pages'
SECTION_NUMBER = 'section number'
SECTION_TITLE = 'section title'


class Variable(Field):
    def __init__(self, type, style=PARENT_STYLE):
        super().__init__(style=style)
        self.type = type

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, self.type)

    def field_spans(self, container):
        text = '?'
        if self.type == PAGE_NUMBER:
            text = str(container.page.number)
        elif self.type == NUMBER_OF_PAGES:
            number = container.document.number_of_pages
            text = str(number)
        elif self.type == SECTION_NUMBER and container.page.section:
            section_id = container.page.section.get_id(container.document)
            text = container.document.get_reference(section_id, REFERENCE) or ''
        elif self.type == SECTION_TITLE and container.page.section:
            section_id = container.page.section.get_id(container.document)
            text = container.document.get_reference(section_id, TITLE)

        field_text = SingleStyledText(text, parent=self)
        return field_text.spans()


class Referenceable(object):
    def __init__(self, id):
        self.id = id

    def prepare(self, document):
        element_id = self.id or document.unique_id
        if self.id is None:
            document.ids_by_element[self] = element_id
        document.elements[element_id] = self
        super().prepare(document)

    def get_id(self, document):
        return self.id or document.ids_by_element[self]

    def update_page_reference(self, page):
        document = page.document
        document.page_references[self.get_id(document)] = page.number


REFERENCE = 'reference'
PAGE = 'page'
TITLE = 'title'
POSITION = 'position'


class Reference(Field):
    def __init__(self, id, type=REFERENCE, style=PARENT_STYLE):
        super().__init__(style=style)
        self.id = id
        self.type = type

    def field_spans(self, container):
        try:
            if self.type == REFERENCE:
                text = container.document.get_reference(self.id, self.type)
                if text is None:
                    self.warn('Cannot reference "{}"'.format(self.id),
                              container)
                    text = ''
            elif self.type == PAGE:
                try:
                    text = str(container.document.page_references[self.id])
                except KeyError:
                    text = '??'
            elif self.type == TITLE:
                text = container.document.get_reference(self.id, self.type)
            else:
                raise NotImplementedError
        except KeyError:
            self.warn("Unknown label '{}'".format(self.id), container)
            text = "??".format(self.id)

        field_text = SingleStyledText(text, parent=self)
        return field_text.spans()


class Note(Referenceable, LabeledFlowable):
    def __init__(self, flowable, id, style=None, parent=None):
        Referenceable.__init__(self, id)
        label = Paragraph('*')
        LabeledFlowable.__init__(self, label, flowable, style=style,
                                 parent=parent)

    def prepare(self, document):
        super().prepare(document)


class RegisterNote(DummyFlowable):
    def __init__(self, note, parent=None):
        super().__init__(parent=parent)
        self.note = note

    def prepare(self, document):
        self.note.prepare(document)


class NoteMarkerStyle(TextStyle, NumberStyle):
    pass


class NoteMarker(Reference):
    style_class = NoteMarkerStyle

    def __init__(self, id, style=None):
        super().__init__(id, style=style)

    def prepare(self, document):
        number_format = self.get_style('number_format', document)
        counter = document.counters.setdefault(__class__, [])
        counter.append(self)
        number = len(counter)
        formatted_number = format_number(number, number_format)
        document.set_reference(self.id, REFERENCE, formatted_number)

    def field_spans(self, container):
        note = container.document.elements[self.id]
        container._footnote_space.add_footnote(note)
        return super().field_spans(container)
        # TODO: handle overflow in footnote_space


class NoteMarkerWithNote(NoteMarker):
    def __init__(self, note, id=None, style=None):
        super().__init__(id, style=style)
        self.note = note

    def prepare(self, document):
        self.note.prepare(document)
        self.id = self.note.get_id(document)
        super().prepare(document)
