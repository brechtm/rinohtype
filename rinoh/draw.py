# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .style import Style, Styled
from .dimension import PT


__all__ = ['Color', 'BLACK', 'WHITE', 'RED', 'GREEN', 'BLUE',
           'Gray', 'GRAY10', 'GRAY25', 'GRAY50', 'GRAY75', 'GRAY90',
           'LineStyle', 'Line', 'Shape', 'Polygon', 'Rectangle']


class Color(object):
    def __init__(self, red, green, blue, alpha=1):
        self.r = red
        self.g = green
        self.b = blue
        self.a = alpha

    @property
    def rgba(self):
        return self.r, self.g, self.b, self.a


class Gray(Color):
    def __init__(self, luminance, alpha=1):
        super().__init__(luminance, luminance, luminance, alpha)


BLACK = Color(0, 0, 0)
WHITE = Color(1, 1, 1)
GRAY10 = Gray(0.10)
GRAY25 = Gray(0.25)
GRAY50 = Gray(0.50)
GRAY75 = Gray(0.75)
GRAY90 = Gray(0.90)
RED = Color(1, 0, 0)
GREEN = Color(0, 1, 0)
BLUE = Color(0, 0, 1)


class LineStyle(Style):
    attributes = {'stroke_width': 1*PT,
                  'stroke_color': BLACK}


class Line(Styled):
    style_class = LineStyle

    def __init__(self, start, end, style=None):
        super().__init__(style)
        self.start = start
        self.end = end

    def render(self, canvas, offset=0):
        points = self.start, self.end
        canvas.line_path(points)
        canvas.stroke(self.get_style('stroke_width', canvas.document),
                      self.get_style('stroke_color', canvas.document))


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

    def render(self, canvas, offset=0):
        canvas.line_path(self.points)
        canvas.close_path()
        canvas.stroke_and_fill(self.get_style('stroke_width', canvas.document),
                               self.get_style('stroke_color', canvas.document),
                               self.get_style('fill_color', canvas.document))


class Rectangle(Polygon):
    def __init__(self, bottom_left, width, height, style=None, parent=None):
        bottom_right = (bottom_left[0] + width, bottom_left[1])
        top_right = (bottom_left[0] + width, bottom_left[1] + height)
        top_left = (bottom_left[0], bottom_left[1] + height)
        points = bottom_left, bottom_right, top_right, top_left
        super().__init__(points, style=style, parent=parent)
