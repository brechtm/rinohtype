
from warnings import warn

from .style import ParentStyle
from .text import StyledText, TextStyle
from .warnings import PyteWarning


class Field(StyledText):
    def __init__(self, style=ParentStyle):
        super().__init__('', style)


class ReferenceField(Field):
    def __init__(self, source):
        self.source = source

    def characters(self):
        for character in self.source.field_characters():
            yield character


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


class Reference(StyledText):
    def __init__(self, id, type=REFERENCE):
        super().__init__('')
        self.id = id
        self.type = type
        self._previous = None

    def characters(self):
        yield ReferenceField(self)

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
        for character in super().characters():
            yield character
