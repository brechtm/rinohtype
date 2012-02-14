
from warnings import warn

from .style import ParentStyle
from .text import StyledText, TextStyle
from .warnings import PyteWarning


class LateEval(object):
    def __init__(self, field):
        self.field = field

    def characters(self):
        return self.field.field_characters()


class Field(StyledText):
    def __init__(self):
        super().__init__('')

    def characters(self):
        yield LateEval(self)

    def field_characters(self):
        return super().characters()


PAGE_NUMBER = 'page number'
NUMBER_OF_PAGES = 'number of pages'
SECTION_NUMBER = 'section number'
SECTION_TITLE = 'section title'


class Variable(Field):
    def __init__(self, type):
        super().__init__()
        self.type = type

    def field_characters(self):
        if self.type == PAGE_NUMBER:
            self.text = str(self.page.number)
        elif self.type == NUMBER_OF_PAGES:
            number = self.document.number_of_pages
            self.text = str(number)
        elif self.type == SECTION_NUMBER:
            if self.page.section and self.page.section.number:
                self.text = self.page.section.number
        elif self.type == SECTION_TITLE:
            if self.page.section:
                self.text = self.page.section.title()
        return super().field_characters()


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
    def __init__(self, id, type=REFERENCE):
        super().__init__()
        self.id = id
        self.type = type

    def field_characters(self):
        try:
            referenced_item = self.document.elements[self.id]
            if self.type == REFERENCE:
                self.text = referenced_item.reference()
            elif self.type == PAGE:
                try:
                    self.text = str(self.document.page_references[self.id])
                except KeyError:
                    self.text = '??'
            elif self.type == TITLE:
                self.text = referenced_item.title()
            else:
                raise NotImplementedError
        except KeyError:
            warn("Unknown label '{}'".format(self.id), PyteWarning)
            self.text = "unkown reference '{}'".format(self.id)

        if self.text is None:
            warn('Trying to reference unreferenceable object', PyteWarning)
            self.text = ' ' #'[not referenceable]'

        return super().field_characters()
