# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
The :class:`Paper` class and a number of predefined paper sizes:

* International: :const:`A0` down to :const:`A10`
* North America: :const:`LETTER`, :const:`LEGAL`, :const:`JUNIOR_LEGAL`,
                 :const:`LEDGER` and :const:`TABLOID`
"""


from .dimension import INCH, MM


__all__ = ['Paper',
           'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10',
           'LETTER', 'LEGAL', 'JUNIOR_LEGAL', 'LEDGER', 'TABLOID']


class Paper(object):
    """Defines a paper size."""

    def __init__(self, width, height):
        """Initialize paper with size `width` and `height`."""
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
