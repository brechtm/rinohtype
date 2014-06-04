# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .annotation import NamedDestination, NamedDestinationLink, AnnotatedSpan
from .flowable import Flowable, LabeledFlowable, DummyFlowable
from .number import NumberStyle, format_number
from .paragraph import Paragraph
from .style import PARENT_STYLE
from .text import SingleStyledText, TextStyle


__all__ = ['Field', 'Variable', 'Referenceable', 'Reference',
           'NoteMarker', 'Note', 'RegisterNote', 'NoteMarkerWithNote',
           'PAGE_NUMBER', 'NUMBER_OF_PAGES', 'SECTION_NUMBER', 'SECTION_TITLE']


class Field(SingleStyledText):
    def __init__(self, style=PARENT_STYLE, parent=None):
        super().__init__('', style=style, parent=parent)


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

    def split(self, container):
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

        return self.split_words(text)


class Referenceable(Flowable):
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
    def __init__(self, target_id, type=REFERENCE, style=PARENT_STYLE):
        super().__init__(style=style)
        self._target_id = target_id
        self.type = type

    def target_id(self, document):
        return self._target_id

    def split(self, container):
        target_id = self.target_id(container.document)
        try:
            if self.type == REFERENCE:
                text = container.document.get_reference(target_id, self.type)
                if text is None:
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
                raise NotImplementedError
        except KeyError:
            self.warn("Unknown label '{}'".format(target_id), container)
            text = "??".format(target_id)

        return self.split_words(text)

    def spans(self):
        annotation = NamedDestinationLink(str(self._target_id))
        return (AnnotatedSpan(span, annotation) for span in super().spans())



class DirectReference(Reference):
    def __init__(self, referenceable, type=REFERENCE, style=PARENT_STYLE):
        super().__init__(None, type=type, style=style)
        self.referenceable = referenceable

    def target_id(self, document):
        return self.referenceable.get_id(document)


class Note(Referenceable, LabeledFlowable):
    def __init__(self, flowable, id=None, style=None, parent=None):
        label = Paragraph(DirectReference(self))
        super().__init__(label, flowable, id=id, style=style, parent=parent)


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

    def __init__(self, target_id, type=REFERENCE, style=None):
        super().__init__(target_id, type=type, style=style)

    def prepare(self, document):
        target_id = self.target_id(document)
        try:  # set reference only once (notes can be referenced multiple times)
            document.get_reference(target_id, REFERENCE)
        except KeyError:
            number_format = self.get_style('number_format', document)
            counter = document.counters.setdefault(__class__, [])
            counter.append(self)
            formatted_number = format_number(len(counter), number_format)
            document.set_reference(target_id, REFERENCE, formatted_number)

    def split(self, container):
        note = container.document.elements[self.target_id(container.document)]
        container._footnote_space.add_footnote(note)
        return super().split(container)
        # TODO: handle overflow in footnote_space


class NoteMarkerWithNote(DirectReference, NoteMarker):
    def __init__(self, note, type=REFERENCE, style=PARENT_STYLE):
        super().__init__(note, type=type, style=style)
        self.note = note

    def prepare(self, document):
        self.note.prepare(document)
        super().prepare(document)
