# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .flowable import Flowable
from .layout import VirtualContainer


__all__ = ['InlineFlowableException', 'InlineFlowable']


class InlineFlowableException(Exception):
    pass


class InlineFlowable(Flowable):
    def font(self, document):
        raise InlineFlowableException

    def y_offset(self, document):
        return 0

    def spans(self, document):
        yield self

    def split(self, container):
        yield self

    def flow_inline(self, container, last_descender, state=None):
        virtual_container = VirtualContainer(container)
        width, _ = self.flow(virtual_container, last_descender, state=state)
        return InlineFlowableSpan(width, virtual_container)


class InlineFlowableSpan(object):
    number_of_spaces = 0
    ends_with_space = False

    def __init__(self, width, virtual_container):
        self.width = width
        self.virtual_container = virtual_container

    def font(self, document):
        raise InlineFlowableException

    @property
    def span(self):
        return self

    def height(self, document):
        return self.virtual_container.cursor

    def ascender(self, document):
        return self.height(document)

    def descender(self, document):
        return 0
