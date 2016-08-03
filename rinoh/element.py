# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .annotation import NamedDestination
from .warnings import warn


__all__ = ['DocumentElement', 'Location']


class Location(object):
    def __init__(self, document_element):
        self.location = document_element.__class__.__name__


class DocumentElement(object):
    """An element that is directly or indirectly part of a :class:`Document`
    and is eventually rendered to the output."""

    def __init__(self, id=None, parent=None, source=None):
        """Initialize this document element as as a child of `parent`
        (:class:`DocumentElement`) if it is not a top-level :class:`Flowable`
        element. `source` should point to a node in the input's document tree
        corresponding to this document element. It is used to point to a
        location in the input file when warnings or errors are generated (see
        the :meth:`warn` method).

        Both parameters are optional, and can be set at a later point by
        assigning to the identically named instance attributes."""
        self.id = id
        self.secondary_ids = []
        self.parent = parent
        self.source = source

    def get_id(self, document, create=True):
        try:
            return self.id or document.ids_by_element[self]
        except KeyError:
            if create:
                return document.register_element(self)

    def get_ids(self, document):
        primary_id = self.get_id(document)
        yield primary_id
        for id in self.secondary_ids:
            yield id

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

    @property
    def elements(self):
        yield self

    def build_document(self, document):
        """Set document metadata and populate front and back matter"""
        pass

    def prepare(self, flowable_target):
        """Determine number labels and register references with the document"""
        if self.get_id(flowable_target.document, create=False):
            flowable_target.document.register_element(self)

    def create_destination(self, container, at_top_of_container=False):
        """Create a destination anchor in the `container` to direct links to
        this :class:`DocumentElement` to."""
        create_destination(self, container, at_top_of_container)

    def warn(self, message, container=None):
        """Present the warning `message` to the user, adding information on the
        location of the related element in the input file."""
        if self.source is not None:
            message = '[{}] '.format(self.source.location) + message
        if container is not None:
            try:
                message += ' (page {})'.format(container.page.formatted_number)
            except AttributeError:
                pass
        warn(message)


def create_destination(flowable, container, at_top_of_container=False):
    """Create a destination anchor in the `container` to direct links to
    `flowable` to."""
    vertical_position = 0 if at_top_of_container else container.cursor
    ids = flowable.get_ids(container.document)
    destination = NamedDestination(*(str(id) for id in ids))
    container.canvas.annotate(destination, 0, vertical_position,
                              container.width, None)
    container.document.register_page_reference(container.page, flowable)
