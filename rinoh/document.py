# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
Classes representing a document:

* :class:`Page`: A single page in a document.
* :class:`Document`: Takes an input file and renders its content onto pages.
* :class:`DocumentElement`: Base class for any element that is eventually
                            rendered in the document.

:class:`Page` require a page orientation to be specified:

* :const:`PORTRAIT`: The page's height is larger than its width.
* :const:`LANDSCAPE`: The page's width is larger than its height.

"""


import datetime
import pickle

from collections import OrderedDict
from itertools import count

from . import __version__, __release_date__
from .backend import pdf
from .flowable import RIGHT, LEFT
from .layout import Container, ReflowRequired
from .number import NUMBER
from .style import DocumentLocationType, Specificity
from .util import NotImplementedAttribute


__all__ = ['Page', 'DocumentPart', 'DocumentSection', 'Document',
           'PageOrientation', 'PORTRAIT', 'LANDSCAPE']


class PageOrientation(str):
    pass


PORTRAIT = PageOrientation('portrait')
LANDSCAPE = PageOrientation('landscape')


class Page(Container):
    """A single page in a document. A :class:`Page` is a :class:`Container`, so
    other containers can be added as children."""

    def __init__(self, document_part, paper, orientation=PORTRAIT):
        """Initialize this page as part of `document` (:class:`Document`) with a
        size defined by `paper` (:class:`Paper`). The page's `orientation` can
        be either :const:`PORTRAIT` or :const:`LANDSCAPE`."""
        self._document_part = document_part
        self.paper = paper
        self.orientation = orientation
        if orientation is PORTRAIT:
            width, height = paper.width, paper.height
        elif orientation is LANDSCAPE:
            width, height = paper.height, paper.width
        document = self.document_part.document
        backend_document = document.backend_document
        self.backend_page = document.backend.Page(self, backend_document,
                                                  width, height)
        self.section = None     # will point to the last section on this page
        self.overflowed_chains = []
        self._current_section = {}
        super().__init__('PAGE', None, 0, 0, width, height)

    @property
    def document_part(self):
        return self._document_part

    def empty_canvas(self):
        self.canvas = self.backend_page.canvas

    @property
    def page(self):
        """Returns the page itself."""
        return self

    def set_current_section(self, section, is_new):
        if (section.level not in self._current_section
            or not self._current_section[section.level][1]):
            self._current_section[section.level] = section, is_new
        for level in list(self._current_section.keys()):
            if level < section.level:
                del self._current_section[level]

    def get_current_section(self, level):
        try:
            section, is_new = self._current_section.get(level)
            return section
        except TypeError:
            return None

    @property
    def document_section(self):
        return self.document_part.document_section

    @property
    def number(self):
        return self.document_section.page_number(self)

    @property
    def number_format(self):
        return self.document_section.page_number_format

    def render(self):
        for index in count():
            try:
                for chain in super().render(rerender=index > 0):
                    yield chain
                break
            except ReflowRequired:
                print('Overflow on page {}, reflowing ({})...'
                      .format(self.number, index + 1))


class BackendDocumentMetadata(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, object_type):
        return instance.backend_document.get_metadata(self.name)

    def __set__(self, instance, value):
        return instance.backend_document.set_metadata(self.name, value)


class DocumentPart(object, metaclass=DocumentLocationType):
    end_at = LEFT

    def __init__(self, document_section):
        self.document_section = document_section
        self.flowable_targets = []
        self.pages = []

    @property
    def document(self):
        return self.document_section.document

    @property
    def number_of_pages(self):
        return len(self.pages)

    def prepare(self):
        for flowable_target in self.flowable_targets:
            flowable_target.prepare(flowable_target)

    def render(self, document_page_count):
        del self.pages[:]
        self.add_page(self.first_page())
        for page in self.pages:
            chains_requiring_new_page = set(chain for chain in page.render())
            page.place()
            if chains_requiring_new_page:
                page = self.new_page(chains_requiring_new_page) # grows self.pages
                self.add_page(page)
        page_count = document_page_count + self.number_of_pages
        next_page_type = LEFT if page_count % 2 else RIGHT
        if next_page_type == self.end_at:
            self.add_page(self.first_page())
        return self.number_of_pages

    def add_page(self, page):
        """Append `page` (:class:`Page`) to this :class:`DocumentPart`."""
        self.pages.append(page)

    def first_page(self):
        raise NotImplementedError

    def new_page(self, chains):
        """Called by :meth:`render` with the :class:`Chain`s that need more
        :class:`Container`s. This method should create a new :class:`Page` which
        contains a container associated with `chain`."""
        raise NotImplementedError

    @classmethod
    def match(cls, styled, container):
        if isinstance(container.document_part, cls):
            return Specificity(1, 0, 0, 0)
        else:
            return None


class DocumentSection(object, metaclass=DocumentLocationType):
    page_number_format = NUMBER
    parts = NotImplementedAttribute()

    def __init__(self, document):
        self.document = document
        self._parts = [part_class(self) for part_class in self.parts]
        self.previous_number_of_pages = 0

    @property
    def number_of_pages(self):
        return sum(part.number_of_pages for part in self._parts)

    @property
    def pages(self):
        return (page for part in self._parts for page in part.pages)

    def page_number(self, this_page):
        for i, page in enumerate(self.pages, start=1):
            if this_page is page:
                return i

    def prepare(self):
        for part in self._parts:
            part.prepare()

    def render(self, doc_page_count):
        section_page_count = 0
        for part in self._parts:
            part_page_count = part.render(doc_page_count + section_page_count)
            section_page_count += part_page_count
        self.previous_number_of_pages = section_page_count
        return section_page_count

    @classmethod
    def match(cls, styled, container):
        if isinstance(container.document_part.document_section, cls):
            return Specificity(1, 0, 0, 0)
        else:
            return None


class Document(object):
    """A document renders the contents described in an input file onto pages.
    This is an abstract base class; subclasses should implement :meth:`setup`
    and :meth:`add_to_chain`."""

    CREATOR = 'RinohType v{} ({})'.format(__version__, __release_date__)

    CACHE_EXTENSION = '.rtc'

    sections = NotImplementedAttribute()

    # FIXME: get backend document metadata from Document metadata
    title = BackendDocumentMetadata('title')
    author = BackendDocumentMetadata('author')
    subject = BackendDocumentMetadata('subject')
    keywords = BackendDocumentMetadata('keywords')

    def __init__(self, content_flowables, stylesheet, backend=pdf):
        """`backend` specifies the backend to use for rendering the document.
        `title`, `author` and `keywords` (iterable of strings) are metadata
        describing the document. These will be written to the output by the
        backend."""
        self._print_version_and_license()
        self.front_matter = []
        self.content_flowables = content_flowables
        self.stylesheet = stylesheet
        self.backend = backend
        self.backend_document = self.backend.Document(self, self.CREATOR)

        self.metadata = dict(title='Document Title',
                             date=datetime.date.today())
        self.counters = {}             # counters for Headings, Figures, Tables
        self.elements = OrderedDict()  # mapping id's to Referenceables
        self.ids_by_element = {}       # mapping elements to id's
        self.references = {}           # mapping id's to reference data
        self.page_references = {}      # mapping id's to page numbers
        self._unique_id = 0

    def _print_version_and_license(self):
        print('RinohType {} ({})  Copyright (c) Brecht Machiels'
              .format(__version__, __release_date__))
        print('''\
This program comes with ABSOLUTELY NO WARRANTY. Its use is subject
to the terms of the GNU Affero General Public License version 3.''')

    @property
    def unique_id(self):
        """Yields a different integer value on each access, used to uniquely
        identify :class:`Referenceable`s for which no identifier was
        specified."""
        self._unique_id += 1
        return self._unique_id

    def set_reference(self, id, reference_type, value):
        id_references = self.references.setdefault(id, {})
        id_references[reference_type] = value

    def get_reference(self, id, reference_type):
        return self.references[id][reference_type]

    def _load_cache(self, filename):
        """Load the cached page references from `<filename>.ptc`."""
        try:
            with open(filename + self.CACHE_EXTENSION, 'rb') as file:
                prev_number_of_pages, prev_page_references = pickle.load(file)
        except (IOError, TypeError):
            prev_number_of_pages, prev_page_references = [], {}
        return prev_number_of_pages, prev_page_references

    def _save_cache(self, filename, section_number_of_pages, page_references):
        """Save the current state of the page references to `<filename>.ptc`"""
        with open(filename + self.CACHE_EXTENSION, 'wb') as file:
            cache = (section_number_of_pages, page_references)
            pickle.dump(cache, file)

    def get_style_var(self, name):
        return self.stylesheet.get_variable(name)

    def render(self, filename_root=None, file=None):
        """Render the document repeatedly until the output no longer changes due
        to cross-references that need some iterations to converge."""
        if filename_root and file is None:
            filename = filename_root + self.backend_document.extension
            file = open(filename, 'wb')
        elif file and filename_root is None:
            filename = getattr(file, 'name', None)
        else:
            raise ValueError("You need to specify either 'filename_root' or "
                             "'file'.")

        def has_converged(section_number_of_pages):
            """Return `True` if the last rendering iteration converged to a
            stable result.

            Practically, this tests whether the total number of pages and page
            references to document elements have changed since the previous
            rendering iteration."""
            nonlocal prev_number_of_pages, prev_page_references
            return (section_number_of_pages == prev_number_of_pages and
                    self.page_references == prev_page_references)

        try:
            for flowable in self.content_flowables:
                flowable.build_document(self)
            (prev_number_of_pages,
             prev_page_references) = self._load_cache(filename_root)
            _sections = [section_cls(self) for section_cls in self.sections]
            for prev_num, section in zip(prev_number_of_pages, _sections):
                section.previous_number_of_pages = prev_num
            self.page_references = prev_page_references.copy()
            for section in _sections:
                section.prepare()
            section_num_pages = self.render_pages(_sections)
            while not has_converged(section_num_pages):
                prev_number_of_pages = section_num_pages
                prev_page_references = self.page_references.copy()
                print('Not yet converged, rendering again...')
                del self.backend_document
                self.backend_document = self.backend.Document(self,
                                                              self.CREATOR)
                section_num_pages = self.render_pages(_sections)
            if filename:
                self._save_cache(filename_root, section_num_pages,
                                 self.page_references)
                print('Writing output: {}'.format(filename))
            self.backend_document.write(file)
        finally:
            if filename_root:
                file.close()


    def render_pages(self, _sections):
        """Render the complete document once and return the number of pages
        rendered."""
        self.floats = set()
        self.placed_footnotes = set()
        section_page_counts = []
        for section in _sections:
            section_page_count = section.render(sum(section_page_counts))
            section_page_counts.append(section_page_count)
        return section_page_counts
