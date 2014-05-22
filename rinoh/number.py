# This file is part of RinohType, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
Functions for formatting numbers:

* :func:`format_number`: Format a number according to a given style.

"""

from .paragraph import ParagraphBase, ParagraphStyle
from .style import Style
from .text import FixedWidthSpace


__all__ = ['NumberStyle', 'NumberedParagraph',
           'NUMBER', 'CHARACTER_LC', 'CHARACTER_UC', 'ROMAN_LC', 'ROMAN_UC',
           'SYMBOL', 'format_number']


NUMBER = 'number'
CHARACTER_LC = 'character'
CHARACTER_UC = 'CHARACTER'
ROMAN_LC = 'roman'
ROMAN_UC = 'ROMAN'
SYMBOL = 'symbol'


def format_number(number, format):
    """Format `number` according the given `format`:

    * :const:`NUMBER`: plain arabic number (1, 2, 3, ...)
    * :const:`CHARACTER_LC`: lowercase letters (a, b, c, ..., aa, ab, ...)
    * :const:`CHARACTER_UC`: uppercase letters (A, B, C, ..., AA, AB, ...)
    * :const:`ROMAN_LC`: lowercase Roman (i, ii, iii, iv, v, vi, ...)
    * :const:`ROMAN_UC`: uppercase Roman (I, II, III, IV, V, VI, ...)

    """
    if format == NUMBER:
        return str(number)
    elif format == CHARACTER_LC:
        string = ''
        while number > 0:
            number, ordinal = divmod(number, 26)
            if ordinal == 0:
                ordinal = 26
                number -= 1
            string = chr(ord('a') - 1 + ordinal) + string
        return string
    elif format == CHARACTER_UC:
        return format_number(number, CHARACTER_LC).upper()
    elif format == ROMAN_LC:
        return romanize(number).lower()
    elif format == ROMAN_UC:
        return romanize(number)
    elif format == SYMBOL:
        return symbolize(number)
    else:
        raise ValueError("Unknown number format '{}'".format(format))


# romanize by Kay Schluehr - from http://billmill.org/python_roman.html

NUMERALS = (('M', 1000), ('CM', 900), ('D', 500), ('CD', 400),
            ('C', 100), ('XC', 90), ('L', 50), ('XL', 40),
            ('X', 10), ('IX', 9), ('V', 5), ('IV', 4), ('I', 1))

def romanize(number):
    """Convert `number` to a Roman numeral."""
    roman = []
    for numeral, value in NUMERALS:
        times, number = divmod(number, value)
        roman.append(times * numeral)
    return ''.join(roman)


SYMBOLS = ('*', '†', '‡', '§', '‖', '¶', '#')

def symbolize(number):
    """Convert `number` to a foot/endnote symbol."""
    repeat, index = divmod(number - 1, len(SYMBOLS))
    return SYMBOLS[index] * (1 + repeat)


class NumberStyle(Style):
    attributes = {'number_format': NUMBER,
                  'number_suffix': '.'}


class NumberedParagraphStyle(ParagraphStyle, NumberStyle):
    pass


class NumberedParagraph(ParagraphBase):
    style_class = NumberedParagraphStyle

    def __init__(self, content, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self.content = content

    def number(self, document):
        number_format = self.get_style('number_format', document)
        if not number_format:
            return ''
        suffix = self.get_style('number_suffix', document)
        formatted_number = DirectReference(self.section, REFERENCE)
        return formatted_number + suffix + FixedWidthSpace()

    def text(self, document):
        raise NotImplementedError


from .reference import DirectReference, REFERENCE
