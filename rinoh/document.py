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


import time
import pickle

from collections import OrderedDict
from itertools import count

from . import __version__, __release_date__
from .layout import FlowableTarget, Container, ReflowRequired
from .backend import pdf
from .warnings import warn


__all__ = ['Page', 'Document', 'DocumentElement', 'PORTRAIT', 'LANDSCAPE']


PORTRAIT = 'portrait'
LANDSCAPE = 'landscape'


class Page(Container):
    """A single page in a document. A :class:`Page` is a :class:`Container`, so
    other containers can be added as children."""

    def __init__(self, document, paper, orientation=PORTRAIT):
        """Initialize this page as part of `document` (:class:`Document`) with a
        size defined by `paper` (:class:`Paper`). The page's `orientation` can
        be either :const:`PORTRAIT` or :const:`LANDSCAPE`."""
        self.paper = paper
        self.orientation = orientation
        if orientation is PORTRAIT:
            width, height = paper.width, paper.height
        elif orientation is LANDSCAPE:
            width, height = paper.height, paper.width
        backend_document = document.backend_document
        self.backend_page = document.backend.Page(self, backend_document,
                                                  width, height)
        self.section = None     # will point to the last section on this page
        self.overflowed_chains = []
        FlowableTarget.__init__(self, document)
        Container.__init__(self, 'PAGE', None, 0, 0, width, height)

    def empty_canvas(self):
        self.canvas = self.backend_page.canvas

    @property
    def page(self):
        """Returns the page itself."""
        return self

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


class DocumentPart(list):
    def __init__(self, document):
        self.document = document

    def render(self, document):
        self.page_count = 0
        self.pages = []
        self.init()
        for page in self.pages:
            chains_requiring_new_page = set(chain for chain in page.render())
            page.place()
            if chains_requiring_new_page:
                self.new_page(chains_requiring_new_page) # this grows self.pages

    def add_page(self, page, number):
        """Add `page` (:class:`Page`) with page `number` (as displayed) to this
        document."""
        page.number = number
        self.pages.append(page)

    # def new_page(self, chains):
    #     assert len(chains) == 1
    #     page = SimplePage(chains[0], self.options['page_size'],
    #                       self.options['page_orientation'])
    #     self.page_count += 1
    #     self.document.add_page(page, self.page_count)
    #     return page.content


class Document(object):
    """A document renders the contents described in an input file onto pages.
    This is an abstract base class; subclasses should implement :meth:`setup`
    and :meth:`add_to_chain`."""

    CREATOR = 'RinohType v{} ({})'.format(__version__, __release_date__)

    CACHE_EXTENSION = '.rtc'

    title = BackendDocumentMetadata('title')
    author = BackendDocumentMetadata('author')
    subject = BackendDocumentMetadata('subject')
    keywords = BackendDocumentMetadata('keywords')

    def __init__(self, stylesheet, backend=pdf, title=None, author=None,
                 subject=None, keywords=None):
        """`backend` specifies the backend to use for rendering the document.
        `title`, `author` and `keywords` (iterable of strings) are metadata
        describing the document. These will be written to the output by the
        backend."""
        self._print_version_and_license()
        self.stylesheet = stylesheet
        self.backend = backend
        self.backend_document = self.backend.Document(self, self.CREATOR)

        self.author = author
        self.title = title
        self.subject = subject
        self.keywords = keywords

        self.parts = []
        self.flowable_targets = []
        self.counters = {}             # counters for Headings, Figures, Tables
        self.elements = OrderedDict()  # mapping id's to Referenceables
        self.ids_by_element = {}       # mapping elements to id's
        self.references = {}           # mapping id's to reference data
        self.number_of_pages = 0       # page count
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

    def add_part(self, part):
        self.parts.append(part)

    def add_page(self, page, number):
        """Add `page` (:class:`Page`) with page `number` (as displayed) to this
        document."""
        page.number = number
        self.pages.append(page)

    def _load_cache(self, filename):
        """Load the cached page references from `<filename>.ptc`."""
        try:
            with open(filename + self.CACHE_EXTENSION, 'rb') as file:
                prev_number_of_pages, prev_page_references = pickle.load(file)
        except IOError:
            prev_number_of_pages, prev_page_references = -1, {}
        return prev_number_of_pages, prev_page_references

    def _save_cache(self, filename):
        """Save the current state of the page references to `<filename>.ptc`"""
        with open(filename + self.CACHE_EXTENSION, 'wb') as file:
            cache = self.number_of_pages, self.page_references
            pickle.dump(cache, file)

    def get_style_var(self, name):
        return self.stylesheet.get_variable(name)

    def render(self, filename):
        """Render the document repeatedly until the output no longer changes due
        to cross-references that need some iterations to converge."""

        def has_converged():
            """Return `True` if the last rendering iteration converged to a
            stable result.

            Practically, this tests whether the total number of pages and page
            references to document elements have changed since the previous
            rendering iteration."""
            nonlocal prev_number_of_pages, prev_page_references
            return (self.number_of_pages == prev_number_of_pages and
                    self.page_references == prev_page_references)

        prev_number_of_pages, prev_page_references = self._load_cache(filename)
        self.number_of_pages = prev_number_of_pages
        self.page_references = prev_page_references.copy()
        for flowable in (flowable for target in self.flowable_targets
                         for flowable in target.flowables):
            flowable.prepare(self)
        self.number_of_pages = self.render_pages()
        while not has_converged():
            prev_number_of_pages = self.number_of_pages
            prev_page_references = self.page_references.copy()
            print('Not yet converged, rendering again...')
            del self.backend_document
            self.backend_document = self.backend.Document(self, self.CREATOR)
            self.number_of_pages = self.render_pages()
        self._save_cache(filename)
        print('Writing output: {}'.format(filename +
                                          self.backend_document.extension))
        self.backend_document.write(filename)

    def render_pages(self):
        """Render the complete document once and return the number of pages
        rendered."""
        # self.pages = []
        self.floats = set()
        self.placed_footnotes = set()
        # self.setup()
        for part in self.parts:
            part.render(self)
        return sum(len(part.pages) for part in self.parts)

    def setup(self):
        """Called by :meth:`render_pages` before the actual rendering takes
        place. This method should create at least one :class:`Page` and add it
        to this document using :meth:`add_page`."""
        raise NotImplementedError

    def new_page(self, chains):
        """Called by :meth:`render_pages` with the :class:`Chain`s that need
        more :class:`Container`s. This method should create a new :class:`Page`
        wich contains a container associated with `chain` and pass it to
        :meth:`add_page`."""
        raise NotImplementedError


class Location(object):
    def __init__(self, document_element):
        self.location = document_element.__class__.__name__


class DocumentElement(object):
    """An element that is directly or indirectly part of a :class:`Document`
    and is eventually rendered to the output."""

    def __init__(self, parent=None, source=None):
        """Initialize this document element as as a child of `parent`
        (:class:`DocumentElement`) if it is not a top-level :class:`Flowable`
        element. `source` should point to a node in the input's document tree
        corresponding to this document element. It is used to point to a
        location in the input file when warnings or errors are generated (see
        the :meth:`warn` method).

        Both parameters are optional, and can be set at a later point by
        assigning to the identically named instance attributes."""
        self.parent = parent
        self.source = source

    @property
    def source(self):
        """The source element this document element was created from."""
        if self._source is not None:
            return self._source
        elif self.parent is not None:
            return self.parent.source
        else:
            return Location(self)

    @source.setter
    def source(self, source):
        """Set `source` as the source element of this document element."""
        self._source = source

    def prepare(self, document):
        pass

    def warn(self, message, container=None):
        """Present the warning `message` to the user, adding information on the
        location of the related element in the input file."""
        if self.source is not None:
            message = '[{}] '.format(self.source.location) + message
        if container is not None:
            message += ' (page {})'.format(container.page.number)
        warn(message)
