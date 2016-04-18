# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from rinoh.document import DocumentPart, DocumentSection
from rinoh.index import IndexSection
from rinoh.number import ROMAN_LC
from rinoh.reference import Variable, PAGE_NUMBER
from rinoh.template import SimplePage, TitlePage
from rinoh.text import Tab


__all__ = ['TitlePart', 'FrontMatterPart', 'ContentsPart',
           'FrontMatter', 'BodyMatter']


# document sections & parts
# ----------------------------------------------------------------------------

class TitlePart(DocumentPart):
    page_template = TitlePage

    def flowables(self):
        return []

    def first_page(self):
        return self.page_template(self)

    def new_page(self, chains):
        assert False, 'TitlePart can consist of only one page!'


class FrontMatterPart(DocumentPart):
    page_template = SimplePage
    footer = Tab() + Variable(PAGE_NUMBER)

    def __init__(self, document_section, flowables):
        self._flowables = flowables
        super().__init__(document_section)

    def flowables(self):
        return self._flowables


class FrontMatter(DocumentSection):
    page_number_format = ROMAN_LC
    parts = [TitlePart]

    def __init__(self, document):
        super().__init__(document)
        for flowables in document.front_matter:
            self._parts.append(FrontMatterPart(self, flowables))


class ContentsPart(DocumentPart):
    page_template = SimplePage

    @property
    def header(self):
        return self.document.options['header_text']

    @property
    def footer(self):
        return self.document.options['footer_text']

    def flowables(self):
        return self.document.content_flowables


class BodyMatter(DocumentSection):
    parts = [ContentsPart]


class IndexPart(DocumentPart):
    page_template = SimplePage

    def flowables(self):
        yield IndexSection()


class BackMatter(DocumentSection):
    parts = [IndexPart]
