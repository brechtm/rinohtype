# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .annotation import NamedDestinationLink, AnnotatedSpan
from .flowable import Flowable, LabeledFlowable, DummyFlowable
from .number import NumberStyle, Label, format_number
from .paragraph import Paragraph
from .text import SingleStyledText, TextStyle
from .util import NotImplementedAttribute


__all__ = ['Field', 'Variable', 'Referenceable', 'Reference',
           'Note', 'RegisterNote',
           'NoteMarkerBase', 'NoteMarkerByID', 'NoteMarkerWithNote',
           'PAGE_NUMBER', 'NUMBER_OF_PAGES', 'SECTION_NUMBER', 'SECTION_TITLE']


class Field(SingleStyledText):
    def __init__(self, style=None, parent=None):
        super().__init__('', style=style, parent=parent)


class Referenceable(Flowable):
    category = NotImplementedAttribute()

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


                            # examples for section "3.2 Some Title"
REFERENCE = 'reference'     # Section 3.2
NUMBER = 'number'           # 3.2
TITLE = 'title'             # Some Title
PAGE = 'page'               # <number of the page on which section 3.2 starts>


class ReferenceBase(Field):
    def __init__(self, type=NUMBER, link=True, quiet=False,
                 style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.type = type
        self.link = link
        self.quiet = quiet

    def target_id(self, document):
        raise NotImplementedError

    def split(self, container):
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

        return self.split_words(text)

    def spans(self, document):
        spans = super().spans(document)
        if self.link:
            annotation = NamedDestinationLink(str(self.target_id(document)))
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


class Note(Referenceable, LabeledFlowable):
    category = 'Note'

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


class NoteMarkerBase(ReferenceBase, Label):
    style_class = NoteMarkerStyle

    def __init__(self, custom_label=None, **kwargs):
        kwargs.update(type=NUMBER, link=True)
        super().__init__(**kwargs)
        Label.__init__(self, custom_label=custom_label)

    def prepare(self, document):
        target_id = self.target_id(document)
        try:  # set reference only once (notes can be referenced multiple times)
            document.get_reference(target_id, NUMBER)
        except KeyError:
            if self.get_style('custom_label', document):
                assert self.custom_label is not None
                formatted_number = str(self.custom_label)
            else:
                number_format = self.get_style('number_format', document)
                counter = document.counters.setdefault(Note.category, [])
                counter.append(self)
                formatted_number = format_number(len(counter), number_format)
            label = self.format_label(str(formatted_number), document)
            document.set_reference(target_id, NUMBER, str(label))

    def before_placing(self, container):
        note = container.document.elements[self.target_id(container.document)]
        container._footnote_space.add_footnote(note)


class NoteMarkerByID(Reference, NoteMarkerBase):
    pass


class NoteMarkerWithNote(DirectReference, NoteMarkerBase):
    def prepare(self, document):
        self.referenceable.prepare(document)
        super().prepare(document)


class FieldType(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.name)


PAGE_NUMBER = FieldType('page number')
NUMBER_OF_PAGES = FieldType('number of pages')


class SectionFieldType(FieldType):
    ref_type = None

    def __init__(self, name, level):
        super().__init__(name)
        self.level = level

    def __repr__(self):
        return "{}('{}', {})".format(self.__class__.__name__, self.name,
                                     self.level)


class SECTION_NUMBER(SectionFieldType):
    ref_type = NUMBER

    def __init__(self, level):
        super().__init__('section number', level)


class SECTION_TITLE(SectionFieldType):
    ref_type = TITLE

    def __init__(self, level):
        super().__init__('section title', level)


class Variable(Field):
    def __init__(self, type, style=None):
        super().__init__(style=style)
        self.type = type

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, self.type)

    def split(self, container):
        if self.type == PAGE_NUMBER:
            text = format_number(container.page.number,
                                 container.page.number_format)
        elif self.type == NUMBER_OF_PAGES:
            document_section = container.document_part.document_section
            number = document_section.previous_number_of_pages
            text = format_number(number, container.page.number_format)
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
        return self.split_words(text)
