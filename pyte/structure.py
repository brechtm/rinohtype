
from pyte.paragraph import ParagraphStyle, Paragraph
from pyte.text import Text

class NumberingStyle:
    number = 0
    character = 1
    Character = 2
    roman = 3
    Roman = 4

class HeadingStyle(ParagraphStyle):
    def __init__(self, indentLeft=None, indentRight=None, indentFirst=None,
                 spaceAbove=None, spaceBelow=None,
                 lineSpacing=None,
                 justify=None,
                 typeface=None, fontStyle=None, fontSize=None, smallCaps=None,
                 hyphenate=None, hyphenChars=None, hyphenLang=None,
                 numberingStyle=None, numberingSeparator=None,
                 base=None):
        ParagraphStyle.__init__(self, indentLeft, indentRight, indentFirst,
                                spaceAbove, spaceBelow,
                                lineSpacing,
                                justify,
                                typeface, fontStyle, fontSize, smallCaps,
                                hyphenate, hyphenChars, hyphenLang,
                                base)
        if numberingStyle is not None: self.numberingStyle = numberingStyle
        if numberingSeparator is not None: self.numberingSeparator = numberingSeparator


HeadingStyle.default = HeadingStyle(base=ParagraphStyle.default,
                                    numberingStyle=NumberingStyle.number,
                                    numberingSeparator='.')

class Heading(Paragraph):
    nextNumber = {}

    def __init__(self, level, title, style=None):
        if style is None:
            style = HeadingStyle.default
        Paragraph.__init__(self, style)
        self.__text = [Text(title, self.style)]
        if level in Heading.nextNumber:
            self._number = Heading.nextNumber[level]
            Heading.nextNumber[level] += 1
        else:
            self._number = 1
            Heading.nextNumber[level] = 2
        self.level = level
        self.title = title

    def _formatNumber(self):
        style = self.style.numberingStyle
        if style == NumberingStyle.number:
            return str(self._number)
        elif style == NumberingStyle.character:
            return chr(ord('a') - 1 + self._number) # TODO: fix number > 26
        elif style == NumberingStyle.Character:
            return chr(ord('A') - 1 + self._number)
        elif style == NumberingStyle.roman:
            return self._romanize(self._number).lower()
        elif style == NumberingStyle.Roman:
            return self._romanize(self._number)

    def _romanize(self, n):
        # by Kay Schluehr - from http://billmill.org/python_roman.html
        numerals = (("M", 1000), ("CM", 900), ("D", 500), ("CD", 400),
                        ("C", 100),("XC", 90),("L", 50),("XL", 40), ("X", 10),
                        ("IX", 9), ("V", 5), ("IV", 4), ("I", 1))
        roman = []
        for ltr, num in numerals:
            (k,n) = divmod(n, num)
            roman.append(ltr*k)
        return "".join(roman)

    def __getattribute__(self, name):
        if name == 'text':
            return self._formatNumber() + ". " + Paragraph.__getattribute__(self, name)
        else:
            return Paragraph.__getattribute__(self, name)


class ListStyle:
    ordered = 0
    unordered = 1

class ListItem(Paragraph):
    pass
