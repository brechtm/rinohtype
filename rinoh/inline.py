# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .dimension import DimensionBase, PT
from .element import DocumentElement
from .flowable import Flowable, FlowableStyle
from .layout import VirtualContainer
from .style import Attribute


__all__ = ['InlineFlowableException', 'InlineFlowable']


class InlineFlowableException(Exception):
    pass


class InlineFlowableStyle(FlowableStyle):
    baseline = Attribute(DimensionBase, 0, 'The offset of the inline flowable '
                                           'relative to the baseline of '
                                           'surrounding text')


class InlineFlowable(Flowable):
    style_class = InlineFlowableStyle

    def __init__(self, baseline=None, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.baseline = baseline

    def font(self, document):
        raise InlineFlowableException

    def y_offset(self, document):
        return 0

    def spans(self, document, **kwargs):
        yield self

    def split(self, container, **kwargs):
        yield self

    def flow_inline(self, container, last_descender, state=None):
        baseline = self.baseline or self.get_style('baseline', container)
        virtual_container = VirtualContainer(container)
        width, _ = self.flow(virtual_container, last_descender, state=state)
        return InlineFlowableSpan(width, baseline, virtual_container)


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
