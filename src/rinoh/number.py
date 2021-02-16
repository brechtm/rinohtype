# This file is part of rinohtype, the Python document preparation system.
#
# Copyright (c) Brecht Machiels.
#
# Use of this source code is subject to the terms of the GNU Affero General
# Public License v3. See the LICENSE file or http://www.gnu.org/licenses/.

"""
Functions for formatting numbers:

* :func:`format_number`: Format a number according to a given style.

"""
from copy import copy

from .attribute import Attribute, OptionSet, Bool
from .style import Style
from .text import StyledText


__all__ = ['NumberFormat', 'NumberStyle', 'Label', 'format_number']


class NumberFormat(OptionSet):
    """How (or if) numbers are displayed"""

    values = (None, 'number', 'symbol', 'lowercase character',
              'uppercase character', 'lowercase roman', 'uppercase roman')


# number: plain arabic numbers (1, 2, 3, ...)
# lowercase character: lowercase letters (a, b, c, ..., aa, ab, ...)
# uppercase character: uppercase letters (A, B, C, ..., AA, AB, ...)
# lowercase roman: lowercase Roman numerals (i, ii, iii, iv, v, vi, ...)
# uppercase roman: uppercase Roman numerals (I, II, III, IV, V, VI, ...)
# symbol: symbols (*, †, ‡, §, ‖, ¶, #, **, *†, ...)


def format_number(number, format):
    """Format `number` according the given `format` (:class:`NumberFormat`)"""
    if format == NumberFormat.NUMBER:
        return str(number)
    elif format == NumberFormat.LOWERCASE_CHARACTER:
        string = ''
        while number > 0:
            number, ordinal = divmod(number, 26)
            if ordinal == 0:
                ordinal = 26
                number -= 1
            string = chr(ord('a') - 1 + ordinal) + string
        return string
    elif format == NumberFormat.UPPERCASE_CHARACTER:
        return format_number(number, 'lowercase character').upper()
    elif format == NumberFormat.LOWERCASE_ROMAN:
        return romanize(number).lower()
    elif format == NumberFormat.UPPERCASE_ROMAN:
        return romanize(number)
    elif format == NumberFormat.SYMBOL:
        return symbolize(number)
    elif format == NumberFormat.NONE:
        return ''
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


class LabelStyle(Style):
    label_prefix = Attribute(StyledText, None, 'Text to prepend to the label')
    label_suffix = Attribute(StyledText, None, 'Text to append to the label')
    custom_label = Attribute(Bool, False, 'Use a custom label if specified')


class Label(object):
    """Mixin class that formats a label

    Args:
        custom_label (StyledText): a frontend can supply a custom label to use
            instead of an automatically determined label (typically a number)

    """

    def __init__(self, custom_label=None):
        self.custom_label = custom_label

    def format_label(self, label, container):
        prefix = self.get_style('label_prefix', container) or ''
        suffix = self.get_style('label_suffix', container) or ''
        return copy(prefix) + copy(label) + copy(suffix)


class NumberStyle(LabelStyle):
    number_format = Attribute(NumberFormat, 'number',
                              'How numbers are formatted')
