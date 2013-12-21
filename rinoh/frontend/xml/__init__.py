# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


import os

from urllib.parse import urljoin
from urllib.request import pathname2url

from ... import DATA_PATH


CATALOG_PATH = os.path.join(DATA_PATH, 'xml', 'catalog')
CATALOG_URL = urljoin('file:', pathname2url(CATALOG_PATH))
CATALOG_NS = "urn:oasis:names:tc:entity:xmlns:xml:catalog"


def element_factory(xml_frontend):
    class CustomElement(xml_frontend.BaseElement):
        def process(self, *args, **kwargs):
            result = self.parse(*args, **kwargs)
            try:
                result.source = self
            except AttributeError:
                pass
            return result

        def parse(self, *args, **kwargs):
            raise NotImplementedError('tag: %s' % self.tag)

        @property
        def location(self):
            tag = self.tag.split('}', 1)[1] if '}' in self.tag else self.tag
            return '{}: <{}> at line {}'.format(self.filename, tag,
                                                self.sourceline)

    class NestedElement(CustomElement):
        def parse(self, *args, **kwargs):
            return self.process_content()

        def process_content(self):
            content = self.text
            for child in self.getchildren():
                content += child.process() + child.tail
            return content

    return CustomElement, NestedElement
