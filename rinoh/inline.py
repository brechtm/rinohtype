# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .element import DocumentElement
from .dimension import PT
from .flowable import Flowable
from .layout import VirtualContainer


__all__ = ['InlineFlowableException', 'InlineFlowable']


class InlineFlowableException(Exception):
    pass


class InlineFlowable(Flowable):
    def __init__(self, baseline=0*PT, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.baseline = baseline

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
        return InlineFlowableSpan(width, self.baseline, virtual_container)


class InlineFlowableSpan(DocumentElement):
    number_of_spaces = 0
    ends_with_space = False

    def __init__(self, width, baseline, virtual_container):
        super().__init__()
        self.width = width
        self.baseline = baseline
        self.virtual_container = virtual_container

    def font(self, document):
        raise InlineFlowableException

    @property
    def span(self):
        return self

    def height(self, document):
        return self.virtual_container.height

    def ascender(self, document):
        return self.height(document) + self.descender(document)

    def descender(self, document):
        return - self.baseline.to_points(self.height(document))

    def line_gap(self, document):
        return 0

    def before_placing(self, container):
        pass

    # TODO: get_style and word_to_glyphs may need proper implementations
    def get_style(self, attribute, document=None):
        pass

    def word_to_glyphs(self, word):
        return word
