# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.



# TODO: split up into weight.py, slant.py and width.py?
# provide aliases (normal, regular, plain, roman)?

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

# slant
UPRIGHT = 'Upright'
OBLIQUE = 'Oblique'
ITALIC = 'Italic'

# width
NORMAL = 'Normal'
CONDENSED = 'Condensed'
EXTENDED = 'Extended'

# position
SUPERSCRIPT = 'Superscript'
SUBSCRIPT = 'Subscript'

# variant
SMALL_CAPITAL = 'Small Capital'
OLD_STYLE = 'Old Style Figure'

WEIGHTS = (HAIRLINE, THIN, ULTRA_LIGHT, EXTRA_LIGHT, LIGHT, BOOK, REGULAR,
           MEDIUM, DEMI_BOLD, BOLD, EXTRA_BOLD, HEAVY, BLACK, EXTRA_BLACK,
           ULTRA_BLACK)
SLANTS = (UPRIGHT, OBLIQUE, ITALIC)
WIDTHS = (NORMAL, CONDENSED, EXTENDED)
POSITIONS = (NORMAL, SUPERSCRIPT, SUBSCRIPT)
VARIANTS = (SMALL_CAPITAL, OLD_STYLE)
