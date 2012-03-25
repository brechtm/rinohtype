
from warnings import warn

from .style import ParentStyle
from .text import StyledText, TextStyle, Superscript
from .warnings import PyteWarning


class LateEval(object):
    def __init__(self, field):
        self.field = field

    def split(self):
        yield self

    def spans(self):
        return self.field.field_spans()


class Field(StyledText):
    def __init__(self, y_offset=0):
        super().__init__('', y_offset=y_offset)

    def spans(self):
        yield LateEval(self)

    def field_spans(self):
        return super().spans()


PAGE_NUMBER = 'page number'
NUMBER_OF_PAGES = 'number of pages'
SECTION_NUMBER = 'section number'
SECTION_TITLE = 'section title'


class Variable(Field):
    def __init__(self, type, y_offset=0):
        super().__init__(y_offset=y_offset)
        self.type = type

    def field_spans(self):
        text = '?'
        if self.type == PAGE_NUMBER:
            text = str(self.page.number)
        elif self.type == NUMBER_OF_PAGES:
            number = self.document.number_of_pages
            text = str(number)
        elif self.type == SECTION_NUMBER:
            if self.page.section and self.page.section.number:
                text = self.page.section.number
        elif self.type == SECTION_TITLE:
            if self.page.section:
                text = self.page.section.title()

        field_text = StyledText(text)
        field_text.parent = self.parent
        return field_text.spans()


class Referenceable(object):
    def __init__(self, document, id):
        if id:
            document.elements[id] = self
        self.id = id

    def reference(self):
        raise NotImplementedError

    def title(self):
        raise NotImplementedError

    def update_page_reference(self):
        self.document.page_references[self.id] = self.page.number


REFERENCE = 'reference'
PAGE = 'page'
TITLE = 'title'
POSITION = 'position'


class Reference(Field):
    def __init__(self, id, type=REFERENCE, y_offset=0):
        super().__init__(y_offset=y_offset)
        self.id = id
        self.type = type

    def field_spans(self):
        try:
            referenced_item = self.document.elements[self.id]
            if self.type == REFERENCE:
                text = referenced_item.reference()
            elif self.type == PAGE:
                try:
                    text = str(self.document.page_references[self.id])
                except KeyError:
                    text = '??'
            elif self.type == TITLE:
                text = referenced_item.title()
            else:
                raise NotImplementedError
        except KeyError:
            warn("Unknown label '{}'".format(self.id), PyteWarning)
            text = "unkown reference '{}'".format(self.id)

        if text is None:
            warn('Trying to reference unreferenceable object', PyteWarning)
            text = ' ' #'[not referenceable]'

        field_text = StyledText(text)
        field_text.parent = self.parent
        return field_text.spans()


class Footnote(Field):
    def __init__(self, note):
        super().__init__()
        self.note = note

    def set_number(self, number):
        self.number = number
        nr = Superscript(str(number) + '  ')
        nr.parent = self.note
        self.note.insert(0, nr)

    def field_spans(self):
        from .paragraph import Paragraph
        field_text = Superscript(str(self.number))
        field_text.parent = self.parent
        return field_text.spans()
