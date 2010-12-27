
from pyte.dimension import Dimension
from pyte.unit import inch, mm

class Paper(object):
    # origin = top left
    #  TODO: make an option for other languages?
    def __init__(self, width, height):
        assert isinstance(width, Dimension)
        assert isinstance(height, Dimension)
        self.width = width
        self.height = height

# define some common paper sizes
Letter = Paper(8.5*inch, 11*inch)
A4 = Paper(210*mm, 297*mm)


