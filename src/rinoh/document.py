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

from pathlib import Path

import datetime
import pickle
import sys
import time

from collections import OrderedDict
from copy import copy
from itertools import count

from . import __version__, __release_date__
from .attribute import OptionSet, Source
from .backend import pdf
from .flowable import StaticGroupedFlowables
from .language import EN
from .layout import (Container, ReflowRequired,
                     BACKGROUND, CONTENT, HEADER_FOOTER)
from .number import format_number
from .strings import Strings
from .style import StyleLog
from .util import RefKeyDictionary
from .warnings import warn


__all__ = ['Page', 'PageOrientation', 'PageType', 'Document', 'DocumentTree']


class DocumentTree(StaticGroupedFlowables):
    """Holds the document's contents as a tree of flowables

    Args:
        flowables (list[Flowable]): the list of top-level flowables
        source_root (Path): path used to locate images and include in logging
            and error and warnings.
        options (Reader): frontend-specific options

    """

    def __init__(self, flowables, options=None):
        super().__init__(flowables)
        self.options = options


class PageOrientation(OptionSet):
    values = 'portrait', 'landscape'


class PageType(OptionSet):
    values = 'left', 'right', 'any'


class Page(Container):
    """A single page in a document.

    A :class:`Page` is a :class:`Container`, so other containers can be added
    as children.

    Args:
        document_part (DocumentPart): the document part this page is part of
        number (int): the 1-based index of this page in the document part
        paper (Paper): determines the dimensions of this page
        orientation (PageOrientation): the orientation of this page

    """

    register_with_parent = False

    def __init__(self, document_part, number, paper, orientation='portrait'):
        self._document_part = document_part
        self.number = number
        self.paper = paper
        self.orientation = orientation
        if orientation == PageOrientation.PORTRAIT:
            width, height = paper.width, paper.height
        elif orientation == PageOrientation.LANDSCAPE:
            width, height = paper.height, paper.width
        document = self.document_part.document
        backend_document = document.backend_document
        self.backend_page = document.backend.Page(backend_document,
                                                  width, height, self.number,
                                                  self.number_format)
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

    def get_current_section(self, level):
        current_section = None
        for section in (section for section in self.document._sections
                        if section.level == level):
            if section.is_hidden(self):
                continue
            section_id = section.get_id(self.document)
            try:
                first_page = self.document.page_elements[section_id]
            except KeyError:
                break
            if first_page.document_part is not self.document_part:
                continue
            elif first_page.number == self.number:
                return section
            elif first_page.number > self.number:
                break
            elif first_page.number <= self.number:
                current_section = section
        return current_section

    @property
    def number_format(self):
        return self.document_part.page_number_format

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


class PartPageCount(object):
    def __init__(self):
        self.count = 0

    def __repr__(self):
        return repr(self.count)

    def __eq__(self, other):
        return self.count == other.count

    def __iadd__(self, other):
        self.count += other
        return self


class Metadata(dict, Source):
    def __init__(self, document, **items):
        super().__init__(**items)
        self._document = document

    def __setitem__(self, key, value):
        try:
            value.source = self
        except AttributeError:
            pass
        super().__setitem__(key, value)

    def __getitem__(self, key):
        return copy(super().__getitem__(key))

    @property
    def location(self):
        return 'document metadata'


class Document(object):
    """Renders a document tree to pages

    Args:
        document_tree (DocumentTree): a tree of the document's contents
        stylesheet (StyleSheet): style sheet used to style document elements
        language (Language): the language to use for standard strings
        strings (Strings): overrides localized strings provided by `language`
        backend: the backend used for rendering the document

    """

    CREATOR = 'rinohtype v{} ({})'.format(__version__, __release_date__)

    CACHE_EXTENSION = '.rtc'

    def __init__(self, document_tree, stylesheet, language, strings=None,
                 backend=None):
        """`backend` specifies the backend to use for rendering the document."""
        super().__init__()
        self._print_version_and_license()
        self.front_matter = []
        self.supporting_matter = {}
        self.document_tree = document_tree
        self.stylesheet = stylesheet
        self.language = language
        self._strings = strings or Strings()
        self.backend = backend or pdf
        self._flowables = list(id(element)
                               for element in document_tree.elements)

        self.metadata = Metadata(self, date=datetime.date.today())
        self.counters = {}             # counters for Headings, Figures, Tables
        self.elements = OrderedDict()  # mapping id's to flowables
        self.ids_by_element = RefKeyDictionary()    # mapping elements to id's
        self.references = {}           # mapping id's to reference data
        self.page_elements = {}        # mapping id's to pages
        self.page_references = {}      # mapping id's to page numbers
        self._sections = []
        self.index_entries = {}
        self._glossary = {}
        self._glossary_first = {}
        self._unique_id = 0
        self.error = False

    def _print_version_and_license(self):
        print('rinohtype {} ({})  Copyright (c) Brecht Machiels and'
              ' contributors'.format(__version__, __release_date__))
        print('''\
This program comes with ABSOLUTELY NO WARRANTY. Its use is subject
to the terms of the GNU Affero General Public License version 3.''')

    def _get_unique_id(self):
        """Yields a different integer value on each access, used to uniquely
        identify :class:`Flowable`s for which no identifier was
        specified."""
        self._unique_id += 1
        return self._unique_id

    def get_metadata(self, key):
        return self.metadata.get(key)

    def register_element(self, element):
        primary_id = (element.get_id(self, create=False)
                      or self._get_unique_id())
        self.ids_by_element[element] = primary_id
        self.elements[primary_id] = element
        for id in element.secondary_ids:
            self.elements[id] = element
        return primary_id

    def register_page_reference(self, page, element):
        for id in element.get_ids(self):
            self.page_elements[id] = page
            self.page_references[id] = page.formatted_number

    def set_reference(self, id, reference_type, value):
        id_references = self.references.setdefault(id, {})
        id_references[reference_type] = value

    def get_reference(self, id, reference_type):
        return self.references[id][reference_type]

    def set_glossary(self, term, definition):
        try:
            existing_definition = self._glossary[term]
            return definition == existing_definition
        except KeyError:
            self._glossary[term] = definition
            return True

    def get_glossary(self, term, id):
        try:
            first_id = self._glossary_first[term]
        except KeyError:
            self._glossary_first[term] = id
            return self._glossary[term], id
        return self._glossary[term], first_id

    def _load_cache(self, filename):
        """Load the cached page references from `<filename>.ptc`."""
        cache_path = filename.with_suffix(self.CACHE_EXTENSION)
        try:
            with cache_path.open('rb') as file:
                part_page_counts, page_references = pickle.load(file)
            print('References cache read from {}'.format(cache_path))
        except (IOError, TypeError):
            part_page_counts, page_references = {}, {}
        return part_page_counts, page_references

    def _save_cache(self, filename):
        """Save the current state of the page references to `<filename>.rtc`"""
        cache_path = Path(filename).with_suffix(self.CACHE_EXTENSION)
        with cache_path.open('wb') as file:
            cache = (self.part_page_counts, self.page_references)
            pickle.dump(cache, file)

    def set_string(self, strings_class, key, value):
        self._strings[strings_class][key] = value

    def get_string(self, strings_class, key):
        if (strings_class in self._strings
                and key in self._strings[strings_class]):
            return self._strings[strings_class][key]
        try:
            return self.language.strings[strings_class][key]
        except KeyError:
            warn('The {} "{}" string is not defined for {} ({}). Using the '
                 'English string instead.'.format(strings_class.__name__, key,
                                                  self.language.name,
                                                  self.language.code))
            return EN.strings[strings_class][key]

    def render(self, filename_root=None, file=None):
        """Render the document repeatedly until the output no longer changes due
        to cross-references that need some iterations to converge."""
        self.error = False
        filename_root = Path(filename_root) if filename_root else None
        if filename_root and file is None:
            extension = self.backend.Document.extension
            filename = filename_root.with_suffix(extension)
            file = filename.open('wb')
        elif file and filename_root is None:
            filename = getattr(file, 'name', None)
        else:
            raise ValueError("You need to specify either 'filename_root' or "
                             "'file'.")

        fake_container = FakeContainer(self)
        prev_page_counts, prev_page_refs = self._load_cache(filename_root)
        metadata_args = {key: self.get_metadata(key)
                         for key in ('title', 'author')}
        try:
            self.document_tree.build_document(fake_container)
            self.prepare(fake_container)
            self.page_elements.clear()
            self.part_page_counts = prev_page_counts
            self.page_references = prev_page_refs.copy()
            while True:
                self.backend_document = self.backend.Document(self.CREATOR,
                                                              **metadata_args)
                self.part_page_counts = self._render_pages()
                if (self.part_page_counts == prev_page_counts
                        and self.page_references == prev_page_refs):
                    break
                print('Not yet converged, rendering again...')
                prev_page_counts = self.part_page_counts
                prev_page_refs = self.page_references.copy()
                del self.backend_document
            self._create_outlines(self.backend_document)
            if filename:
                self._save_cache(filename_root)
                self.style_log.write_log(filename_root)
                print('Writing output: {}'.format(filename))
            self.backend_document.write(file)
        finally:
            if filename_root:
                file.close()
        return not self.error

    def _render_pages(self):
        """Render the complete document once and return the number of pages
        rendered."""
        self.style_log = StyleLog(self.stylesheet)
        self.floats = set()
        self.placed_footnotes = set()
        self._start_time = time.time()

        part_page_counts = {}
        part_page_count = PartPageCount()
        last_number_format = None
        for part_template in self.part_templates:
            part = part_template.document_part(self)
            if part is None:
                continue
            if part_template.page_number_format != last_number_format:
                part_page_count = PartPageCount()
            part_page_count += part.render(part_page_count.count + 1)
            part_page_counts[part_template.name] = part_page_count
            last_number_format = part_template.page_number_format
        sys.stdout.write('\n')     # for the progress indicator
        return part_page_counts

    def _create_outlines(self, backend_document):
        """Create an outline in the output file that allows for easy navigation
        of the document. The outline is a hierarchical tree of all the sections
        in the document."""
        sections = parent = []
        current_level = 1
        stack = []
        fake_container = FakeContainer(self)
        for section in self._sections:
            if not section.show_in_toc(fake_container):
                continue
            section_id = section.get_id(self, create=False)
            section_number = self.get_reference(section_id, 'number')
            section_title = self.get_reference(section_id, 'title')
            if section.level > current_level:
                if section.level != current_level + 1:
                    warn("Your document section hierarchy is missing levels. "
                         "Please report this at https://github.com/brechtm"
                         "/rinohtype/pull/67")
                    break
                stack.append(parent)
                parent = current
            elif section.level < current_level:
                for i in range(current_level - section.level):
                    parent = stack.pop()
            current = []
            item = (str(section_id), section_number, section_title, current)
            parent.append(item)
            current_level = section.level
        backend_document.create_outlines(sections)

    PROGRESS_TEMPLATE = \
        '\r{:3d}% [{}{}] ETA {:02d}:{:02d} ({:02d}:{:02d}) page {}'
    PROGRESS_BAR_WIDTH = 40

    def progress(self, flowable, container):
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
            sys.stdout.write(self.PROGRESS_TEMPLATE
                             .format(int(percent), filled * '=',
                                     (self.PROGRESS_BAR_WIDTH - filled) * ' ',
                                     eta // 60, eta % 60,
                                     passed // 60, passed % 60,
                                     container.page.formatted_number))
            sys.stdout.flush()


class FakeContainer(object):    # TODO: clean up
    def __init__(self, document):
        self.document = document
