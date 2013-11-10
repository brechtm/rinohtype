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

from itertools import count

from . import __version__, __release_date__
from .layout import FlowableTarget, Container, ReflowRequired
from .backend import pdf
from .warnings import warn


__all__ = ['Page', 'Document', 'DocumentElement', 'PORTRAIT', 'LANDSCAPE']


PORTRAIT = 'portrait'
LANDSCAPE = 'landscape'


try:
    profile
except NameError:
    def profile(function):
        return function


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
        FlowableTarget.__init__(self, document)
        Container.__init__(self, 'PAGE', None, 0, 0, width, height)
        backend_document = self.document.backend_document
        self.backend_page = document.backend.Page(self, backend_document,
                                                  self.width, self.height)
        self.section = None     # will point to the last section on this page
        self.overflowed_chains = []
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


class Document(object):
    """A document renders the contents described in an input file onto pages.
    This is an abstract base class; subclasses should implement :meth:`setup`
    and :meth:`add_to_chain`."""

    _cache_extension = '.ptc'

    def __init__(self, backend=pdf, title=None, author=None, keywords=None):
        """`backend` specifies the backend to use for rendering the document.
        `title`, `author` and `keywords` (iterable of strings) are metadata
        describing the document. These will be written to the output by the
        backend."""
        self._print_version_and_license()
        self.backend = backend
        self.backend_document = self.backend.Document(self, title)

        self.author = author
        self.title = title
        self.keywords = keywords
        self.creator = "RinohType"
        self.creation_time = time.asctime()

        self.counters = {}      # counters for Headings, Figures and Tables
        self.elements = {}      # mapping id's to Referenceables
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

    def add_page(self, page, number):
        """Add `page` (:class:`Page`) with page `number` (as displayed) to this
        document."""
        page.number = number
        self.pages.append(page)

    def _load_cache(self, filename):
        """Load the cached page references from `<filename>.ptc`."""
        try:
            with open(filename + self._cache_extension, 'rb') as file:
                self.number_of_pages, self.page_references = pickle.load(file)
                self._previous_number_of_pages = self.number_of_pages
                self._previous_page_references = self.page_references.copy()
        except IOError:
            self.number_of_pages = 0
            self._previous_number_of_pages = -1
            self.page_references = {}
            self._previous_page_references = {}

    def _save_cache(self, filename):
        """Save the current state of the page references to `<filename>.ptc`"""
        with open(filename + self._cache_extension, 'wb') as file:
            cache = self.number_of_pages, self.page_references
            pickle.dump(cache, file)

    def _has_converged(self):
        """Return `True` if the last rendering iteration converged to a stable
        result.

        Practically, this tests whether the total number of pages and page
        references to document elements have changed since the previous
        rendering iteration."""
        return (self.number_of_pages == self._previous_number_of_pages and
                self.page_references == self._previous_page_references)

    def render(self, filename):
        """Render the document repeatedly until the output no longer changes due
        to cross-references that need some iterations to converge."""
        self._load_cache(filename)
        self.number_of_pages = self.render_pages()
        while not self._has_converged():
            self._previous_number_of_pages = self.number_of_pages
            self._previous_page_references = self.page_references.copy()
            print('Not yet converged, rendering again...')
            del self.backend_document
            self.backend_document = self.backend.Document(self, self.title)
            self.number_of_pages = self.render_pages()
        self._save_cache(filename)
        print('Writing output: {}'.format(filename +
                                          self.backend_document.extension))
        self.backend_document.write(filename)

    def render_pages(self):
        """Render the complete document once and return the number of pages
        rendered."""
        self.pages = []
        self.floats = set()
        self.setup()
        for page in self.pages:
            chains_requiring_new_page = set(chain for chain in page.render())
            page.place()
            if chains_requiring_new_page:
                self.new_page(chains_requiring_new_page) # this grows self.pages
        return len(self.pages)

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


class DocumentElement(object):
    """An element that is directly or indirectly part of a :class:`Document`
    and is eventually rendered to the output."""

    def __init__(self, document=None, parent=None, source=None):
        """Initialize this document element as an element of `document`
        (:class:`Document`) or as child of `parent` (:class:`DocumentElement`).
        `source` should point to a node in the input's document tree
        corresponding to this document element. It is used to point to a
        location in the input file when warnings or errors are generated (see
        the :meth:`warn` method).

        All three parameters are optional, and can be set at a later point by
        assinging to the identically named instance attributes."""
        self.document = document
        self.parent = parent
        self.source = source

    @property
    def document(self):
        """The document this element belongs to."""
        if self._document is not None:
            return self._document
        else:
            return self.parent.document

    @document.setter
    def document(self, document):
        """Set `document` as owner of this element."""
        self._document = document

    @property
    def source(self):
        """The source element this document element was created from."""
        if self._source is not None:
            return self._source
        else:
            return self.parent.source

    @source.setter
    def source(self, source):
        """Set `source` as the source element of this document element."""
        self._source = source

    def warn(self, message, container):
        """Present the warning `message` to the user, adding information on the
        location of the related element in the input file."""
        if self.source is not None:
            message = '[{}] '.format(self.source.location) + message
        message += ' (page {})'.format(container.page.number)
        warn(message)
