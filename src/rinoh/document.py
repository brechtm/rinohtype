# This file is part of rinohtype, the Python document preparation system.
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
import os
import pickle
import sys
import time

from collections import OrderedDict
from itertools import count

from . import __version__, __release_date__
from .backend import pdf
from .flowable import RIGHT, LEFT, StaticGroupedFlowables
from .layout import (Container, ReflowRequired, Chain, PageBreakException,
                     BACKGROUND, CONTENT, HEADER_FOOTER)
from .number import NUMBER, format_number
from .reference import TITLE
from .structure import NewChapterException, Section
from .style import DocumentLocationType, Specificity, StyleLog
from .util import NotImplementedAttribute, RefKeyDictionary


__all__ = ['Page', 'DocumentPart', 'DocumentSection', 'Document',
           'PageOrientation', 'PORTRAIT', 'LANDSCAPE']


class DocumentTree(StaticGroupedFlowables):
    def __init__(self, source_file, flowables):
        super().__init__(flowables)
        self.source_file = source_file

    @property
    def source_root(self):
        return os.path.abspath(os.path.dirname(self.source_file))


class PageOrientation(str):
    pass


PORTRAIT = PageOrientation('portrait')
LANDSCAPE = PageOrientation('landscape')


class Page(Container):
    """A single page in a document. A :class:`Page` is a :class:`Container`, so
    other containers can be added as children."""

    register_with_parent = False

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
        self.backend_page = document.backend.Page(backend_document,
                                                  width, height, self.number,
                                                  self.number_format)
        self.section = None     # will point to the last section on this page
        self.overflowed_chains = []
        self._current_section = {}
        self._empty = True
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

    def set_current_section(self, section, heading):
        if heading:
            if (section.level not in self._current_section
                    or not self._current_section[section.level][1]):
                self._current_section[section.level] = section, True
        elif section.level not in self._current_section:
            self._current_section[section.level] = section, False

    def get_current_section(self, level):
        current_section = None
        for id, section in ((id, element)
                            for id, element in self.document.elements.items()
                            if (isinstance(element, Section)
                                and element.level == level)):
            try:
                first_page = self.document.page_references[id]
            except KeyError:
                break
            if first_page == self.number:
                return section
            elif first_page > self.number:
                break
            elif first_page <= self.number:
                current_section = section
        return current_section

    @property
    def document_section(self):
        return self.document_part.document_section

    @property
    def number(self):
        return self.document_section.page_number(self)

    @property
    def number_format(self):
        return self.document_section.page_number_format

    @property
    def formatted_number(self):
        return format_number(self.number, self.number_format)

    def render(self):
        super().render(BACKGROUND)
        try:
            for index in count():
                try:
                    super().render(CONTENT, rerender=index > 0)
                    break
                except ReflowRequired:
                    print('Overflow on page {}, reflowing ({})...'
                          .format(self.number, index + 1))
        finally:
            super().render(HEADER_FOOTER)

    def place(self):
        self.before_placing()
        self.place_children()
        self.canvas.place_annotations()


class BackendDocumentMetadata(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, object_type):
        return instance.backend_document.get_metadata(self.name)

    def __set__(self, instance, value):
        return instance.backend_document.set_metadata(self.name, value)


class DocumentPart(object, metaclass=DocumentLocationType):
    """Part of a :class:`DocumentSection` that has a specific page template."""

    header = None
    footer = None
    end_at = LEFT

    def __init__(self, document_section,
                 right_page_template, left_page_template, flowables):
        self.document_section = document_section
        self.right_page_template = right_page_template
        self.left_page_template = left_page_template or right_page_template
        self.flowable_targets = []
        self.pages = []
        if flowables:
            self.chain = Chain(self)
            for flowable in flowables:
                self.chain << flowable
        else:
            self.chain = None

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
            try:
                page.render()
                break_type = None
            except NewChapterException as nce:
                break_type = nce.break_type
            except PageBreakException as pbe:
                break_type = None
            page.place()
            if self.chain and not self.chain.done:
                next_page_type = LEFT if page.number % 2 else RIGHT
                page = self.new_page(next_page_type == break_type)
                self.add_page(page)     # this grows self.pages!
        page_count = document_page_count + self.number_of_pages
        next_page_type = LEFT if page_count % 2 else RIGHT
        if next_page_type == self.end_at:
            self.add_page(self.first_page())
        return self.number_of_pages

    def add_page(self, page):
        """Append `page` (:class:`Page`) to this :class:`DocumentPart`."""
        self.pages.append(page)

    def first_page(self):
        return self.new_page(new_chapter=True)

    def new_page(self, new_chapter, **kwargs):
        """Called by :meth:`render` with the :class:`Chain`s that need more
        :class:`Container`s. This method should create a new :class:`Page` which
        contains a container associated with `chain`."""
        page_template = (self.left_page_template if len(self.pages) % 2
                         else self.right_page_template)
        return page_template.page(self, page_template.name, self.chain,
                                  new_chapter, **kwargs)

    @classmethod
    def match(cls, styled, container):
        if isinstance(container.document_part, cls):
            return Specificity(0, 1, 0, 0, 0)
        else:
            return None


class DocumentSection(object, metaclass=DocumentLocationType):
    """A section of a :class:`Document` that has its own page numbering."""

    parts = NotImplementedAttribute()

    def __init__(self, document, page_number_format=NUMBER):
        self.document = document
        self.page_number_format = page_number_format
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
            return Specificity(0, 1, 0, 0, 0)
        else:
            return None


class Document(object):
    """A document renders the contents described in an input file onto pages.
    This is an abstract base class; subclasses should implement :meth:`setup`
    and :meth:`add_to_chain`."""

    CREATOR = 'rinohtype v{} ({})'.format(__version__, __release_date__)

    CACHE_EXTENSION = '.rtc'

    sections = NotImplementedAttribute()

    # FIXME: get backend document metadata from Document metadata
    title = BackendDocumentMetadata('title')
    author = BackendDocumentMetadata('author')
    subject = BackendDocumentMetadata('subject')
    keywords = BackendDocumentMetadata('keywords')

    def __init__(self, document_tree, stylesheet, strings=None,
                 backend=pdf):
        """`backend` specifies the backend to use for rendering the document."""
        self._print_version_and_license()
        self.front_matter = []
        self.document_tree = document_tree
        self.stylesheet = stylesheet
        self._strings = strings or ()
        self.backend = backend
        self.backend_document = self.backend.Document(self.CREATOR)
        self._flowables = list(id(element)
                               for element in document_tree.elements)

        self.metadata = dict(title='Document Title',
                             date=datetime.date.today())
        self.counters = {}             # counters for Headings, Figures, Tables
        self.elements = OrderedDict()  # mapping id's to flowables
        self.ids_by_element = RefKeyDictionary()    # mapping elements to id's
        self.references = {}           # mapping id's to reference data
        self.page_references = {}      # mapping id's to page numbers
        self.last_page_references = {}
        self.index_entries = {}
        self._unique_id = 0

    def _print_version_and_license(self):
        print('rinohtype {} ({})  Copyright (c) Brecht Machiels'
              .format(__version__, __release_date__))
        print('''\
This program comes with ABSOLUTELY NO WARRANTY. Its use is subject
to the terms of the GNU Affero General Public License version 3.''')

    def _get_unique_id(self):
        """Yields a different integer value on each access, used to uniquely
        identify :class:`Flowable`s for which no identifier was
        specified."""
        self._unique_id += 1
        return self._unique_id

    def register_element(self, element):
        primary_id = (element.get_id(self, create=False)
                      or self._get_unique_id())
        self.ids_by_element[element] = primary_id
        self.elements[primary_id] = element
        return primary_id

    def register_page_reference(self, page, element):
        for id in element.get_ids(self):
            self.page_references[id] = page.number

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

    def strings(self, strings_class):
        for strings in self._strings:
            if isinstance(strings, strings_class):
                return strings
        return strings_class()

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
            self.document_tree.build_document(self)
            (prev_number_of_pages,
             prev_page_references) = self._load_cache(filename_root)
            _sections = [section for section in self.sections]
            for prev_num, section in zip(prev_number_of_pages, _sections):
                section.previous_number_of_pages = prev_num
            self.page_references = prev_page_references.copy()
            for section in _sections:
                section.prepare()
            section_num_pages = self._render_pages(_sections)
            while not has_converged(section_num_pages):
                prev_number_of_pages = section_num_pages
                prev_page_references = self.page_references.copy()
                print('Not yet converged, rendering again...')
                del self.backend_document
                self.backend_document = self.backend.Document(self.CREATOR)
                section_num_pages = self._render_pages(_sections)
            self.create_outlines()
            if filename:
                self._save_cache(filename_root, section_num_pages,
                                 self.page_references)
                self.style_log.write_log(filename_root)
                print('Writing output: {}'.format(filename))
            self.backend_document.write(file)
        finally:
            if filename_root:
                file.close()

    def create_outlines(self):
        sections = parent = []
        current_level = 1
        stack = []
        for section_id, section in ((id, flowable)
                                    for id, flowable in self.elements.items()
                                    if isinstance(flowable, Section)):
            section_number = self.get_reference(section_id, NUMBER)
            section_title = self.get_reference(section_id, TITLE)
            if section.level > current_level:
                assert section.level == current_level + 1
                stack.append(parent)
                parent = current
            elif section.level < current_level:
                for i in range(current_level - section.level):
                    parent = stack.pop()
            current = []
            item = (str(section_id), section_number, section_title, current)
            parent.append(item)
            current_level = section.level
        self.backend_document.create_outlines(sections)

    def _render_pages(self, _sections):
        """Render the complete document once and return the number of pages
        rendered."""
        self.style_log = StyleLog(self.stylesheet)
        self.floats = set()
        self.placed_footnotes = set()
        section_page_counts = []
        self._start_time = time.time()
        for section in _sections:
            section_page_count = section.render(sum(section_page_counts))
            section_page_counts.append(section_page_count)
        sys.stdout.write('\n')     # for the progress indicator
        return section_page_counts

    PROGRESS_BAR_WIDTH = 40

    def progress(self, flowable):
        try:
            index = self._flowables.index(id(flowable))
        except ValueError:
            pass
        else:
            percent = 100 * (index + 1) / len(self._flowables)
            time_passed = time.time() - self._start_time
            passed = int(time_passed)
            eta = int(time_passed / percent * (100 - percent))
            filled = int(self.PROGRESS_BAR_WIDTH * percent / 100)
            sys.stdout.write('\r{:3d}% [{}{}] ETA {:02d}:{:02d} ({:02d}:{:02d})'
                             .format(int(percent), filled * '=',
                                     (self.PROGRESS_BAR_WIDTH - filled) * ' ',
                                     eta // 60, eta % 60,
                                     passed // 60, passed % 60))
            sys.stdout.flush()
