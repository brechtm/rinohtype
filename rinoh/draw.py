# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from .color import BLACK, GRAY90
from .style import Style, Styled
from .dimension import PT


__all__ = ['LineStyle', 'Line', 'Shape', 'Polygon', 'Rectangle']


class LineStyle(Style):
    attributes = {'stroke_width': 1*PT,
                  'stroke_color': BLACK}


class Line(Styled):
    style_class = LineStyle

    def __init__(self, start, end, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.start = start
        self.end = end

    def render(self, container, offset=0):
        canvas, document = container.canvas, container.document
        stroke_width = self.get_style('stroke_width', container)
        stroke_color = self.get_style('stroke_color', container)
        if not (stroke_width and stroke_color):
            return
        with canvas.save_state():
            points = self.start, self.end
            canvas.line_path(points)
            canvas.stroke(stroke_width, stroke_color)


class ShapeStyle(LineStyle):
    attributes = {'fill_color': GRAY90}


class Shape(Styled):
    style_class = ShapeStyle

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)

    def render(self, canvas, offset=0):
        raise NotImplementedError


class Polygon(Shape):
    def __init__(self, points, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.points = points

    def render(self, container, offset=0):
        canvas = container.canvas
        stroke_width = self.get_style('stroke_width', container)
        stroke_color = self.get_style('stroke_color', container)
        fill_color = self.get_style('fill_color', container)
        if not ((stroke_width and stroke_color) or fill_color):
            return
        with canvas.save_state():
            canvas.line_path(self.points)
            canvas.close_path()
            if stroke_width and stroke_color and fill_color:
                canvas.stroke_and_fill(stroke_width, stroke_color,
                                       fill_color)
            elif stroke_width and stroke_color:
                canvas.stroke(stroke_width, stroke_color)
            elif fill_color:
                canvas.fill(fill_color)


class Rectangle(Polygon):
    def __init__(self, bottom_left, width, height, style=None, parent=None):
        bottom_right = (bottom_left[0] + width, bottom_left[1])
        top_right = (bottom_left[0] + width, bottom_left[1] + height)
        top_left = (bottom_left[0], bottom_left[1] + height)
        points = bottom_left, bottom_right, top_right, top_left
        super().__init__(points, style=style, parent=parent)
