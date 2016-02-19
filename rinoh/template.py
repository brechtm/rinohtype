# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from rinoh.document import Document, DocumentSection, PageOrientation, PORTRAIT
from .dimension import DimensionBase, CM
from .paper import Paper, A4
from .reference import (Variable, SECTION_NUMBER, SECTION_TITLE, PAGE_NUMBER,
                        NUMBER_OF_PAGES)
from .text import MixedStyledText, Tab
from .style import StyleSheet
from .util import NamedDescriptor, WithNamedDescriptors


from rinohlib.stylesheets import sphinx


__all__ = ['DocumentTemplate', 'DocumentOptions', 'Option']


class Option(NamedDescriptor):
    """Descriptor used to describe a document option"""
    def __init__(self, accepted_type, default_value, description):
        self.accepted_type = accepted_type
        self.default_value = default_value
        self.description = description

    def __get__(self, document_options, type=None):
        try:
            return document_options.get(self.name, self.default_value)
        except AttributeError:
            return self

    def __set__(self, document_options, value):
        if not isinstance(value, self.accepted_type):
            raise TypeError('The {} document option only accepts {} instances'
                            .format(self.name, self.accepted_type))
        document_options[self.name] = value

    @property
    def __doc__(self):
        return (':description: {} (:class:`{}`)\n'
                ':default: {}'
                .format(self.description, self.accepted_type.__name__,
                        self.default_value))


class DocumentOptions(dict, metaclass=WithNamedDescriptors):
    """Collects options to customize a :class:`DocumentTemplate`. Options are
    specified as keyword arguments (`options`) matching the class's
    attributes."""

    stylesheet = Option(StyleSheet, sphinx.stylesheet,
                        'The stylesheet to use for styling document elements')
    page_size = Option(Paper, A4, 'The format of the pages in the document')
    page_orientation = Option(PageOrientation, PORTRAIT,
                              'The orientation of pages in the document')
    page_horizontal_margin = Option(DimensionBase, 3*CM, 'The margin size on '
                                    'the left and the right of the page')
    page_vertical_margin = Option(DimensionBase, 3*CM, 'The margin size on the '
                                  'top and bottom of the page')
    columns = Option(int, 1, 'The number of columns for the body text')
    show_date = Option(bool, True, "Show or hide the document's date")
    show_author = Option(bool, True, "Show or hide the document's author")
    header_text = Option(MixedStyledText, Variable(SECTION_NUMBER(1))
                                          + ' ' + Variable(SECTION_TITLE(1)),
                         'The text to place in the page header')
    footer_text = Option(MixedStyledText, Tab() + Variable(PAGE_NUMBER)
                                          + '/' + Variable(NUMBER_OF_PAGES),
                         'The text to place in the page footer')

    def __init__(self, **options):
        for name, value in options.items():
            option_descriptor = getattr(type(self), name, None)
            if not isinstance(option_descriptor, Option):
                raise AttributeError('No such document option: {}'.format(name))
            setattr(self, name, value)

    def __getitem__(self, name):
        return getattr(self, name)



class DocumentTemplateSection(DocumentSection):
    parts = []


class DocumentTemplate(Document):
    options_class = DocumentOptions

    def __init__(self, flowables, document_parts, options=None, backend=None):
        self.options = options or self.options_class()
        self.document_parts = document_parts
        super().__init__(flowables, self.options['stylesheet'], backend=backend)

    @property
    def sections(self):
        current_section = None
        for document_part_tmpl in self.document_parts:
            if not current_section or document_part_tmpl.restart_numbering:
                if current_section:
                    yield current_section
                current_section = DocumentTemplateSection(self)
            part = document_part_tmpl.document_part(current_section)
            current_section._parts.append(part)
        yield current_section
