
from warnings import warn

from .text import SingleStyledText, TextStyle, Superscript
from .warnings import PyteWarning


class LateEval(object):
    def __init__(self, field):
        self.field = field

    def split(self):
        yield self

    def spans(self, container):
        return self.field.field_spans(container)


class Field(SingleStyledText):
    def __init__(self):
        super().__init__('')

    def spans(self):
        yield LateEval(self)

    def field_spans(self):
        return super().spans()


PAGE_NUMBER = 'page number'
NUMBER_OF_PAGES = 'number of pages'
SECTION_NUMBER = 'section number'
SECTION_TITLE = 'section title'


class Variable(Field):
    def __init__(self, type):
        super().__init__()
        self.type = type

    def field_spans(self, container):
        text = '?'
        if self.type == PAGE_NUMBER:
            text = str(container.page.number)
        elif self.type == NUMBER_OF_PAGES:
            number = self.document.number_of_pages
            text = str(number)
        elif self.type == SECTION_NUMBER:
            if container.page.section and container.page.section.number:
                text = container.page.section.number
        elif self.type == SECTION_TITLE:
            if container.page.section:
                text = container.page.section.title()

        field_text = SingleStyledText(text)
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

    def update_page_reference(self, page):
        self.document.page_references[self.id] = page.number


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
            referenced_item = self.document.elements[self.id]
            if self.type == REFERENCE:
                text = referenced_item.reference()
                if text is None:
                    self.warn('Cannot reference "{}"'.format(referenced_item))
                    text = ''
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
            self.warn("Unknown label '{}'".format(self.id))
            text = "??".format(self.id)

        field_text = SingleStyledText(text)
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

    def field_spans(self, container):
        self.set_number(container._footnote_space.next_number)
        self.note.document = self.document
        self.note.flow(container._footnote_space)
        field_text = Superscript(str(self.number))
        field_text.parent = self.parent
        return field_text.spans()
