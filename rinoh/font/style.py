# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

from ..attribute import OptionSet


__all__ = ['FontWeight', 'HAIRLINE', 'THIN', 'ULTRA_LIGHT', 'EXTRA_LIGHT',
           'LIGHT', 'BOOK', 'REGULAR', 'MEDIUM', 'DEMI_BOLD', 'BOLD',
           'EXTRA_BOLD', 'HEAVY', 'BLACK', 'EXTRA_BLACK', 'ULTRA_BLACK',
           'FontSlant', 'UPRIGHT', 'OBLIQUE', 'ITALIC',
           'FontWidth', 'NORMAL', 'CONDENSED', 'EXTENDED',
           'FontVariant', 'SMALL_CAPITAL', 'OLD_STYLE',
           'TextPosition', 'SUPERSCRIPT', 'SUBSCRIPT']


# weight
HAIRLINE = 'Hairline'
THIN = 'Thin'
ULTRA_LIGHT = 'Ultra-Light'
EXTRA_LIGHT = 'Extra-Light'
LIGHT = 'Light'
BOOK = 'Book'
REGULAR = 'Regular'
MEDIUM = 'Medium'
DEMI_BOLD = 'Demi-Bold'
BOLD = 'Bold'
EXTRA_BOLD = 'Extra-Bold'
HEAVY = 'Heavy'
BLACK = 'Black'
EXTRA_BLACK = 'Extra-Black'
ULTRA_BLACK = 'Ultra-Black'

class FontWeight(OptionSet):
    values = (HAIRLINE, THIN, ULTRA_LIGHT, EXTRA_LIGHT, LIGHT, BOOK, REGULAR,
              MEDIUM, DEMI_BOLD, BOLD, EXTRA_BOLD, HEAVY, BLACK, EXTRA_BLACK,
              ULTRA_BLACK)


# slant
UPRIGHT = 'Upright'
OBLIQUE = 'Oblique'
ITALIC = 'Italic'

class FontSlant(OptionSet):
    values = UPRIGHT, OBLIQUE, ITALIC
    alternatives = {UPRIGHT: (OBLIQUE, ITALIC),
                    OBLIQUE: (ITALIC, UPRIGHT),
                    ITALIC: (OBLIQUE, UPRIGHT)}


# width
NORMAL = 'Normal'
CONDENSED = 'Condensed'
EXTENDED = 'Extended'

class FontWidth(OptionSet):
    values = NORMAL, CONDENSED, EXTENDED
    alternatives = {NORMAL: (CONDENSED, EXTENDED),
                    CONDENSED: (NORMAL, EXTENDED),
                    EXTENDED: (NORMAL, CONDENSED)}


# variant
SMALL_CAPITAL = 'Small Capital'
OLD_STYLE = 'Oldstyle Figures'

class FontVariant(OptionSet):
    values = NORMAL, SMALL_CAPITAL, OLD_STYLE


# position
SUPERSCRIPT = 'Superscript'
SUBSCRIPT = 'Subscript'

class TextPosition(OptionSet):
    values = NORMAL, SUPERSCRIPT, SUBSCRIPT
