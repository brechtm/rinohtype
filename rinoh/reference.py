# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from copy import copy
from warnings import warn

from .text import StyledText, SingleStyledText, Superscript


__all__ = ['FieldException', 'Referenceable',
           'Field', 'Variable', 'Reference', 'Footnote',
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
    def __init__(self, type):
        super().__init__()
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

        field_text = SingleStyledText(text)
        field_text.parent = self.parent
        return field_text.spans()


class Referenceable(object):
    def __init__(self, document, id):
        self.id = id

    def prepare(self, document):
        element_id = self.id or document.unique_id
        document.elements[element_id] = self
        document.ids_by_element[self] = element_id

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
    def __init__(self, id, type=REFERENCE):
        super().__init__()
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

        field_text = SingleStyledText(text)
        field_text.parent = self.parent
        return field_text.spans()


class Footnote(Field):
    def __init__(self, note):
        super().__init__()
        self.note = note

    def field_spans(self, container):
        number = container._footnote_space.next_number
        note = copy(self.note)
        nr = Superscript(str(number) + '  ')
        nr.parent = note
        note.insert(0, nr)
        note.document = container.document
        note.flow(container._footnote_space, None)
        field_text = Superscript(str(number))
        field_text.parent = self.parent
        return field_text.spans()
