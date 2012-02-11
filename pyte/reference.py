
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
        return super().field_characters()


class ReferenceNotConverged(Exception):
    pass


class Referenceable(object):
    def __init__(self, document, id):
        if id:
            document.elements[id] = self
        self.id = id

    def reference(self):
        raise NotImplementedError

    def title(self):
        raise NotImplementedError


REFERENCE = 'reference'
PAGE = 'page'
TITLE = 'title'
POSITION = 'position'


class Reference(Field):
    def __init__(self, id, type=REFERENCE):
        super().__init__()
        self.id = id
        self.type = type
        self._previous = None

    def field_characters(self):
        try:
            referenced_item = self.document.elements[self.id]
            if self.type == REFERENCE:
                self.text = referenced_item.reference()
            elif self.type == PAGE:
                try:
                    page_number = referenced_item.page.number
                    if self._previous != page_number:
                        self._previous = page_number
                        raise AttributeError
                    self.text = str(page_number)
                except AttributeError:
                    self.document.converged = False
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
