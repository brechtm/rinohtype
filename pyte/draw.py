
from .style import Style, Styled
from .unit import pt


class Color(object):
    def __init__(self, r, g, b, a=1):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @property
    def rgba(self):
        return self.r, self.g, self.b, self.a


BLACK = Color(0, 0, 0)
WHITE = Color(1, 1, 1)
RED = Color(1, 0, 0)
GREEN = Color(0, 1, 0)
BLUE = Color(0, 0, 1)


class LineStyle(Style):
    attributes = {'width': 1*pt,
                  'color': BLACK}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Line(Styled):
    style_class = LineStyle

    def __init__(self, start, end, style=None):
        super().__init__(style)
        self.start = start
        self.end = end

    def render(self, canvas, offset=0):
        points = self.start, self.end
        canvas.line_path(points)
        canvas.stroke(self.get_style('width'), self.get_style('color'))


class Shape(Styled):
    style_class = LineStyle

    def __init__(self, style=None):
        super().__init__(style)

    def render(self, canvas, offset=0):
        raise NotImplementedError


class Polygon(Shape):
    def __init__(self, points, style=None):
        super().__init__(style)
        self.points = points

    def render(self, canvas, offset=0):
        canvas.line_path(self.points)
        canvas.stroke(self.get_style('width'), self.get_style('color'))


class Rectangle(Polygon):
    def __init__(self, bottom_left, width, height, style=None):
        bottom_right = (bottom_left[0] + width, bottom_left[1])
        top_right = (bottom_left[0] + width, bottom_left[1] + height)
        top_left = (bottom_left[0], bottom_left[1] + height)
        points = bottom_left, bottom_right, top_right, top_left
        super().__init__(points, style)
