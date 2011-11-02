
from .style import NUMBER, CHARACTER_LC, CHARACTER_UC, ROMAN_LC, ROMAN_UC


def format_number(number, style):
    if style == NUMBER:
        return str(number)
    elif style == CHARACTER_LC:
        string = ''
        while number > 26:
            number, remainder = divmod(number, 26)
            if remainder == 0:
                remainder = 26
                number -= 1
            string = chr(ord('a') - 1 + remainder) + string
        return chr(ord('a') - 1 + number) + string
    elif style == CHARACTER_UC:
        return format_number(number, CHARACTER_LC).upper()
    elif style == ROMAN_LC:
        return romanize(number).lower()
    elif style == ROMAN_UC:
        return romanize(number)
    else:
        raise ValueError("Unknown numbering style '{}'".format(style))


def romanize(n):
    # by Kay Schluehr - from http://billmill.org/python_roman.html
    numerals = (("M", 1000), ("CM", 900), ("D", 500), ("CD", 400),
                ("C", 100),("XC", 90),("L", 50),("XL", 40), ("X", 10),
                ("IX", 9), ("V", 5), ("IV", 4), ("I", 1))
    roman = []
    for ltr, num in numerals:
        (k, n) = divmod(n, num)
        roman.append(ltr * k)
    return "".join(roman)
