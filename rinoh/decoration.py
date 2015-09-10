# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .draw import Rectangle, Line, ShapeStyle
from .layout import EndOfContainer, InlineDownExpandingContainer
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
        draw_top = state is None or state.initial
        try:
            container.advance(self.get_style('padding_top', document))
            left = self.get_style('padding_left', document)
            right = container.width - self.get_style('padding_right', document)
            padding_bottom = float(self.get_style('padding_bottom', document))
            with InlineDownExpandingContainer('PADDING', container, left=left,
                    right=right, extra_space_below=padding_bottom) as pad_cntnr:
                _, descender = self.flowable.flow(pad_cntnr, descender, state=state)
            self.render_frame(container, container.height, top=draw_top)
            return container.width, descender
        except EndOfContainer as eoc:
            if eoc.flowable_state and not eoc.flowable_state.initial:
                self.render_frame(container, container.max_height,
                                  top=draw_top, bottom=False)
            raise

    def render_frame(self, container, container_height, top=True, bottom=True):
        width, height = float(container.width), - float(container_height)
        fill_style = ShapeStyle(base=PARENT_STYLE, stroke_color=None)
        rect = Rectangle((0, 0), width, height, style=fill_style, parent=self)
        rect.render(container)
        style = dict(style=PARENT_STYLE, parent=self)
        if top:
            Line((0, 0), (width, 0), **style).render(container)
        Line((0, 0), (0, height), **style).render(container)          # left
        Line((width, 0), (width, height), **style).render(container)  # right
        if bottom:
            Line((0, height), (width, height), **style).render(container)
