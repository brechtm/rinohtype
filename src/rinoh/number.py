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

from .attribute import Attribute, OptionSet, Bool
from .paragraph import ParagraphBase, ParagraphStyle
from .style import Style
from .text import StyledText

__all__ = ['NumberStyle', 'Label', 'NumberedParagraph',
           'NUMBER', 'CHARACTER_LC', 'CHARACTER_UC', 'ROMAN_LC', 'ROMAN_UC',
           'SYMBOL', 'format_number']


NUMBER = 'number'
CHARACTER_LC = 'lowercase character'
CHARACTER_UC = 'uppercase character'
ROMAN_LC = 'lowercase roman'
ROMAN_UC = 'uppercase roman'
SYMBOL = 'symbol'


class NumberFormat(OptionSet):
    values = (NUMBER, CHARACTER_LC, CHARACTER_UC, ROMAN_LC, ROMAN_UC, SYMBOL,
              None)


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


class LabelStyle(Style):
    label_prefix = Attribute(StyledText, None, 'Text to prepend to the label')
    label_suffix = Attribute(StyledText, None, 'Text to append to the label')
    custom_label = Attribute(Bool, False, 'Use a cutom label if specified')


class Label(object):
    def __init__(self, custom_label=None):
        self.custom_label = custom_label

    def format_label(self, label, container):
        prefix = self.get_style('label_prefix', container) or ''
        suffix = self.get_style('label_suffix', container) or ''
        return prefix + label + suffix


class NumberStyle(LabelStyle):
    number_format = Attribute(NumberFormat, NUMBER, 'How numbers are formatted')


class NumberedParagraphStyle(ParagraphStyle, NumberStyle):
    pass


class NumberedParagraph(ParagraphBase, Label):
    style_class = NumberedParagraphStyle

    def __init__(self, content, custom_label=None,
                 id=None, style=None, parent=None):
        super().__init__(id=id, style=style, parent=parent)
        Label.__init__(self, custom_label=custom_label)
        self.content = content

    def to_string(self, flowable_target):
        text = self.text(flowable_target)
        return ''.join(item.to_string(flowable_target) for item in text)

    @property
    def referenceable(self):
        raise NotImplementedError

    def number(self, container):
        document = container.document
        target_id = self.referenceable.get_id(document)
        formatted_number = document.get_reference(target_id, NUMBER)
        if formatted_number:
            return self.format_label(formatted_number, container)
        else:
            return ''

    def text(self, container):
        raise NotImplementedError


from .reference import NUMBER
