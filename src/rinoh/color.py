# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

import binascii
import struct

from itertools import repeat

from .attribute import AcceptNoneAttributeType, ParseError

__all__ = ['Color', 'HexColor', 'BLACK', 'WHITE', 'RED', 'GREEN', 'BLUE',
           'Gray', 'GRAY10', 'GRAY25', 'GRAY50', 'GRAY75', 'GRAY90']


class Color(AcceptNoneAttributeType):
    """Color defined by component values

    Args:
        red (float): red component (0 .. 1)
        blue (float): blue component (0 .. 1)
        green (float): green component (0 .. 1)
        alpha (float): opacity (0 .. 1)

    """

    def __init__(self, red, green, blue, alpha=1):
        for value in (red, green, blue, alpha):
            if not 0 <= value <= 1:
                raise ValueError('Color component values can range from 0 to 1')
        self.r = red
        self.g = green
        self.b = blue
        self.a = alpha

    def __str__(self):
        rgba_bytes = struct.pack(4 * 'B', *(int(c * 255) for c in self.rgba))
        string = binascii.hexlify(rgba_bytes).decode('ascii')
        if string.endswith('ff'):
            string = string[:-2]
        if string[::2] == string[1::2]:
            string = string[::2]
        return '#' + string

    def __repr__(self):
        return '{}({}, {}, {}, {})'.format(type(self).__name__, *self.rgba)

    @property
    def rgba(self):
        return self.r, self.g, self.b, self.a

    @classmethod
    def parse_string(cls, string, source):
        try:
            return HexColor(string)
        except ValueError:
            raise ParseError("'{}' is not a valid {}. Must be a HEX string."
                             .format(string, cls.__name__))

    @classmethod
    def doc_format(cls):
        return ('HEX string with optional alpha component '
                '(``#RRGGBB``, ``#RRGGBBAA``, ``#RGB`` or ``#RGBA``)')


class HexColor(Color):
    """Color defined as a hexadecimal string

    Args:
        string (str): ``#RGBA`` or ``#RRGGBBAA`` (``#`` and ``A`` are optional)

    """
    def __init__(self, string):
        if string.startswith('#'):
            string = string[1:]
        if len(string) in (3, 4):
            string = ''.join(repeated for char in string
                             for repeated in repeat(char, 2))
        string = string.encode('ascii')
        try:
            r, g, b = struct.unpack('BBB', binascii.unhexlify(string[:6]))
            if string[6:]:
                a, = struct.unpack('B', binascii.unhexlify(string[6:]))
            else:
                a = 255
        except (struct.error, binascii.Error):
            raise ValueError('Bad color string passed to ' +
                             self.__class__.__name__)
        super().__init__(*(value / 255 for value in (r, g, b, a)))


class Gray(Color):
    """Shade of gray

    Args:
        luminance (float): brightness (0 .. 1)
        alpha (float): opacity (0 .. 1)

    """
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
