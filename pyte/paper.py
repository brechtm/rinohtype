
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


# International (DIN 476 / ISO 216)
A0 = Paper(841*mm, 1189*mm)
A1 = Paper(594*mm, 841*mm)
A2 = Paper(420*mm, 594*mm)
A3 = Paper(297*mm, 420*mm)
A4 = Paper(210*mm, 297*mm)
A5 = Paper(148*mm, 210*mm)
A6 = Paper(105*mm, 148*mm)
A7 = Paper(74*mm, 105*mm)
A8 = Paper(52*mm, 74*mm)
A9 = Paper(37*mm, 52*mm)
A10 = Paper(26*mm, 37*mm)


# North America
LETTER = Paper(8.5*inch, 11*inch)
LEGAL = Paper(8.5*inch, 14*inch)
JUNIOR_LEGAL = Paper(8*inch, 5*inch)
LEDGER = Paper(17*inch, 11*inch)
TABLOID = Paper(11*inch, 17*inch)
