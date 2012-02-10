
from warnings import warn

from .text import StyledText
from .warnings import PyteWarning


class Field(object):
    def __init__(self, source):
        self.source = source

    def characters(self):
        for character in self.source.field_characters():
            yield character


class ReferenceNotConverged(Exception):
    pass


class Referenceable(object):
    def __init__(self, document, id):
        self.document = document
        if id:
            document.elements[id] = self
        self.id = id

    def reference(self):
        raise NotImplementedError

    def title(self):
        raise NotImplementedError

    def page(self):
        try:
            page = self._page
            if self._previous_page is not None and self._previous_page != page:
                raise ReferenceNotConverged
            return str(page)
        except AttributeError:
            raise ReferenceNotConverged


REFERENCE = 'reference'
PAGE = 'page'
TITLE = 'title'
POSITION = 'position'


class Reference(StyledText):
    def __init__(self, document, id, type=REFERENCE):
        super().__init__('')
        self.document = document
        self.id = id
        self.type = type

    def characters(self):
        yield Field(self)

    def field_characters(self):
        try:
            referenced_item = self.document.elements[self.id]
            if self.type == REFERENCE:
                self.text = referenced_item.reference()
            elif self.type == PAGE:
                try:
                    self.text = referenced_item.page()
                except ReferenceNotConverged:
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
