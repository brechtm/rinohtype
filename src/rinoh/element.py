# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .annotation import NamedDestination
from .warnings import warn


__all__ = ['DocumentElement']


class DocumentElement(object):
    """A element part of the document to be rendered

    Args:
        id (str): unique identifier for referencing this element
        parent (DocumentElement): element of which this element is a child
        source (Source): object identifying where this document element is
            defined; used for resolving relative paths, logging or error
            reporting

    """

    def __init__(self, id=None, parent=None, source=None):
        self.id = id
        self.secondary_ids = []
        self.parent = parent
        self.source = source

    @property
    def source_root(element):
        while element.parent:
            if element.source:
                return element.source.root
            element = element.parent

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
    def elements(self):
        yield self

    def build_document(self, flowable_target):
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
