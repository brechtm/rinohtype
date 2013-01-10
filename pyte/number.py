"""
Functions for formatting numbers:

* :func:`format_number`: Format a number according to a given style.

"""


__all__ = ['NUMBER', 'CHARACTER_LC', 'CHARACTER_UC', 'ROMAN_LC', 'ROMAN_UC',
           'format_number']


NUMBER = 'number'
CHARACTER_LC = 'character'
CHARACTER_UC = 'CHARACTER'
ROMAN_LC = 'roman'
ROMAN_UC = 'ROMAN'


def format_number(number, style):
    """Format `number` according the given `style`.

    `style` can be:

    * :const:`NUMBER`: plain arabic number (1, 2, 3, ...)
    * :const:`CHARACTER_LC`: lowercase letters (a, b, c, ..., aa, ab, ...)
    * :const:`CHARACTER_UC`: uppercase letters (A, B, C, ..., AA, AB, ...)
    * :const:`ROMAN_LC`: lowercase Roman (i, ii, iii, iv, v, vi, ...)
    * :const:`ROMAN_UC`: uppercase Roman (I, II, III, IV, V, VI, ...)

    """
    if style == NUMBER:
        return str(number)
    elif style == CHARACTER_LC:
        string = ''
        while number > 0:
            number, ordinal = divmod(number, 26)
            if ordinal == 0:
                ordinal = 26
                number -= 1
            string = chr(ord('a') - 1 + ordinal) + string
        return string
    elif style == CHARACTER_UC:
        return format_number(number, CHARACTER_LC).upper()
    elif style == ROMAN_LC:
        return romanize(number).lower()
    elif style == ROMAN_UC:
        return romanize(number)
    else:
        raise ValueError("Unknown numbering style '{}'".format(style))


# romanize by Kay Schluehr - from http://billmill.org/python_roman.html

NUMERALS = (('M', 1000), ('CM', 900), ('D', 500), ('CD', 400),
            ('C', 100),('XC', 90),('L', 50),('XL', 40),
            ('X', 10), ('IX', 9), ('V', 5), ('IV', 4), ('I', 1))

def romanize(number):
    """Convert `number` to a Roman numeral."""
    roman = []
    for numeral, value in NUMERALS:
        times, number = divmod(number, value)
        roman.append(times * numeral)
    return ''.join(roman)
