# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .draw import Rectangle, ShapeStyle
from .layout import DownExpandingContainer, EndOfContainer
from .flowable import Flowable, FlowableStyle
from .style import PARENT_STYLE


__all__ = ['FrameStyle', 'Framed']


class FrameStyle(FlowableStyle, ShapeStyle):
    attributes = {'padding_left': 10,
                  'padding_right': 10,
                  'padding_top': 10,
                  'padding_bottom': 10}


class Framed(Flowable):
    style_class = FrameStyle

    def __init__(self, flowable, id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        self.flowable = flowable
        flowable.parent = self

    def render(self, container, descender, state=None):
        document = container.document
        try:
            container.advance(self.get_style('padding_top', document))
            left = self.get_style('padding_left', document)
            right = container.width - self.get_style('padding_right', document)
            pad_container = DownExpandingContainer('PADDING', container,
                                                   left=left, right=right)
            _, descender = self.flowable.flow(pad_container, descender,
                                              state=state)
            container.advance(pad_container.cursor
                              + self.get_style('padding_bottom', document))
            self.render_frame(container, container.height)
            return container.width, descender
        except EndOfContainer:
            self.render_frame(container, container.max_height)
            raise

    def render_frame(self, container, container_height):
        width, height = float(container.width), - float(container_height)
        rect = Rectangle((0, 0), width, height, style=PARENT_STYLE, parent=self)
        rect.render(container.canvas)
