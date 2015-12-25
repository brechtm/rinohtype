# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .warnings import warn


__all__ = ['DocumentElement', 'Location']


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

    def build_document(self, document):
        """Set document metadata and populate front and back matter"""
        pass

    def prepare(self, flowable_target):
        """Determine number labels and register references with the document"""
        pass

    def warn(self, message, container=None):
        """Present the warning `message` to the user, adding information on the
        location of the related element in the input file."""
        if self.source is not None:
            message = '[{}] '.format(self.source.location) + message
        if container is not None:
            message += ' (page {})'.format(container.page.number)
        warn(message)
