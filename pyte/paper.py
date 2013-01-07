
from pyte.dimension import Dimension
from pyte.dimension import INCH, MM


class Paper(object):
    # origin = top left
    #  TODO: make an option for other languages?
    def __init__(self, width, height):
        assert isinstance(width, Dimension)
        assert isinstance(height, Dimension)
        self.width = width
        self.height = height


# International (DIN 476 / ISO 216)
A0 = Paper(841*MM, 1189*MM)
A1 = Paper(594*MM, 841*MM)
A2 = Paper(420*MM, 594*MM)
A3 = Paper(297*MM, 420*MM)
A4 = Paper(210*MM, 297*MM)
A5 = Paper(148*MM, 210*MM)
A6 = Paper(105*MM, 148*MM)
A7 = Paper(74*MM, 105*MM)
A8 = Paper(52*MM, 74*MM)
A9 = Paper(37*MM, 52*MM)
A10 = Paper(26*MM, 37*MM)


# North America
LETTER = Paper(8.5*INCH, 11*INCH)
LEGAL = Paper(8.5*INCH, 14*INCH)
JUNIOR_LEGAL = Paper(8*INCH, 5*INCH)
LEDGER = Paper(17*INCH, 11*INCH)
TABLOID = Paper(11*INCH, 17*INCH)
