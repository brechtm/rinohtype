"""

* :class:`Page`:
* :class:`Document`:
* :class:`DocumentElement`:

"""


import time
import pickle

from .layout import FlowableTarget, Container
from .backend import pdf
from .warnings import warn


PORTRAIT = 'portrait'
LANDSCAPE = 'landscape'


class Page(Container):
    """A single page in a document."""

    def __init__(self, document, paper, orientation=PORTRAIT):
        """Initialize this page as part of `document` with a size defined by
        `paper`. The `orientation` can be :const:`PORTRAIT` or
        :const:`LANDSCAPE`."""
        self.paper = paper
        self.orientation = orientation
        if orientation is PORTRAIT:
            width, height = paper.width, paper.height
        elif orientation is LANDSCAPE:
            width, height = paper.height, paper.width
        FlowableTarget.__init__(self, document)
        Container.__init__(self, None, 0, 0, width, height)
        self.backend = document.backend
        backend_document = self.document.backend_document
        self.backend_page = self.backend.Page(self, backend_document,
                                              self.width, self.height)
        self.section = None

    @property
    def page(self):
        """Returns the page itself."""
        return self

    @property
    def canvas(self):
        """The canvas associated with this page."""
        return self.backend_page.canvas


class Document(object):
    """A document accepts an input file and renders it onto pages."""

    _cache_extension = '.ptc'

    def __init__(self, parser, filename, backend=pdf):
        """Initialize the document, reading the file with `filename` as input,
        using `parser` is used to parse the input.

        `backend` specifies the backend to use for rendering the document."""
        self.xml = parser.parse(filename)
        self.root = self.xml.getroot()

        self.creator = "pyTe"
        self.author = None
        self.title = None
        self.keywords = []
        self.created = time.asctime()

        self.backend = backend
        self.backend_document = self.backend.Document(self, self.title)
        self.counters = {}
        self.elements = {}
        self._unique_id = 0

    @property
    def unique_id(self):
        self._unique_id += 1
        return self._unique_id

    def load_cache(self, filename):
        try:
            file = open(filename + self._cache_extension, 'rb')
            self.number_of_pages, self.page_references = pickle.load(file)
            self._previous_number_of_pages = self.number_of_pages
            self._previous_page_references = self.page_references.copy()
            file.close()
        except IOError:
            self.number_of_pages = 0
            self._previous_number_of_pages = -1
            self.page_references = {}
            self._previous_page_references = {}

    def save_cache(self, filename):
        file = open(filename + self._cache_extension, 'wb')
        data = (self.number_of_pages, self.page_references)
        pickle.dump(data, file)
        file.close()

    def add_page(self, page, number):
        assert isinstance(page, Page)
        self.pages.append(page)
        page.number = number

    def has_converged(self):
        return (self.number_of_pages == self._previous_number_of_pages and
                self.page_references == self._previous_page_references)

    def render(self, filename):
        self.load_cache(filename)
        self.number_of_pages = self.render_pages()
        while not self.has_converged():
            self._previous_number_of_pages = self.number_of_pages
            self._previous_page_references = self.page_references.copy()
            print('Not yet converged, rendering again...')
            del self.backend_document
            self.backend_document = self.backend.Document(self, self.title)
            self.number_of_pages = self.render_pages()
        self.save_cache(filename)
        print('Writing output: {}'.format(filename +
                                          self.backend_document.extension))
        self.backend_document.write(filename)

    def render_pages(self):
        self.pages = []
        self.setup()
        index = 0
        while index < len(self.pages):
            page = self.pages[index]
            index += 1
            for chain in page.render():
                self.add_to_chain(chain)
            page.place()
        return len(self.pages)

    def setup(self):
        raise NotImplementedError

    def add_to_chain(self, chain):
        raise NotImplementedError


class DocumentElement(object):
    """An element that is directly or indirectly part of a :class:`Document`
    and is eventually rendered to the output."""

    def __init__(self, document=None, parent=None):
        """Initialize this document element as a child of `parent`."""
        self._document = document
        self.parent = parent

    @property
    def document(self):
        """The document this element belongs to."""
        if self._document is not None:
            return self._document
        else:
            return self.parent.document

    @document.setter
    def document(self, document):
        """"""
        self._document = document

    def warn(self, message):
        if hasattr(self, '_source'):
            message = '[{}] {}'.format(self._source.location, message)
        warn(message)
