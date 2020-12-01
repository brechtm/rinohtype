# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.


from .attribute import Attribute, AcceptNoneAttributeType, ParseError
from .color import Color, BLACK, GRAY90
from .style import Style, Styled
from .dimension import Dimension, PT


__all__ = ['Stroke', 'LineStyle', 'Line', 'ShapeStyle', 'Shape',
           'Polygon', 'Rectangle']


class Stroke(AcceptNoneAttributeType):
    """The display properties of a line

    Args:
        width (Dimension): the width of the line
        color (Color): the color of the line

    """

    def __init__(self, width, color):
        self.width = width
        self.color = color

    def __str__(self):
        return '{}, {}'.format(self.width, self.color)

    def __repr__(self):
        return '{}({}, {})'.format(type(self).__name__, repr(self.width),
                                   repr(self.color))

    @classmethod
    def check_type(cls, value):
        if value and not (Dimension.check_type(value.width)
                          and Color.check_type(value.color)):
            return False
        return super().check_type(value)

    @classmethod
    def parse_string(cls, string, source):
        try:
            width_str, color_str = (part.strip() for part in string.split(','))
        except ValueError:
            raise ParseError('Expecting stroke width and color separated by a '
                             'comma')
        width = Dimension.from_string(width_str)
        color = Color.from_string(color_str)
        return cls(width, color)

    @classmethod
    def doc_format(cls):
        return ('the width (:class:`.Dimension`) and color (:class:`.Color`) '
                'of the stroke, separated by a comma (``,``)')


class LineStyle(Style):
    stroke = Attribute(Stroke, Stroke(1*PT, BLACK), 'Width and color used to '
                                                    'draw the line')


class Line(Styled):
    """Draws a line

    Args:
        start (2-tuple): coordinates for the start point of the line
        end (2-tuple): coordinates for the end point of the line

    """

    style_class = LineStyle

    def __init__(self, start, end, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.start = start
        self.end = end

    def render(self, container, offset=0):
        canvas, document = container.canvas, container.document
        stroke = self.get_style('stroke', container)
        if not stroke:
            return
        with canvas.save_state():
            points = self.start, self.end
            canvas.line_path(points)
            canvas.stroke(stroke.width, stroke.color)


class ShapeStyle(LineStyle):
    fill_color = Attribute(Color, GRAY90, 'Color to fill the shape')


class Shape(Styled):
    """Base class for closed shapes"""

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
        stroke = self.get_style('stroke', container)
        fill_color = self.get_style('fill_color', container)
        if not (stroke or fill_color):
            return
        with canvas.save_state():
            canvas.line_path(self.points)
            canvas.close_path()
            if stroke and fill_color:
                canvas.stroke_and_fill(stroke.width, stroke.color,
                                       fill_color)
            elif stroke:
                canvas.stroke(stroke.width, stroke.color)
            elif fill_color:
                canvas.fill(fill_color)


class Rectangle(Polygon):
    def __init__(self, bottom_left, width, height, style=None, parent=None):
        bottom_right = (bottom_left[0] + width, bottom_left[1])
        top_right = (bottom_left[0] + width, bottom_left[1] + height)
        top_left = (bottom_left[0], bottom_left[1] + height)
        points = bottom_left, bottom_right, top_right, top_left
        super().__init__(points, style=style, parent=parent)
