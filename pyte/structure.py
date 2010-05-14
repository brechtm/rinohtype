
from pyte.paragraph import ParagraphStyle, Paragraph, DefaultStyle
from pyte.unit import nil


class NumberingStyle:
    number = 0
    character = 1
    Character = 2
    roman = 3
    Roman = 4

class HeadingStyle(ParagraphStyle):
    def __init__(self, name="", indentLeft=None, indentRight=None, indentFirst=None,
                 spaceAbove=None, spaceBelow=None,
                 lineSpacing=None,
                 justify=None,
                 typeface=None, fontStyle=None, fontSize=None, smallCaps=None,
                 hyphenate=None, hyphenChars=None, hyphenLang=None,
                 numberingStyle=None, numberingSeparator=None,
                 base=None):
        ParagraphStyle.__init__(self, name, indentLeft, indentRight, indentFirst,
                                spaceAbove, spaceBelow,
                                lineSpacing,
                                justify,
                                typeface, fontStyle, fontSize, smallCaps,
                                hyphenate, hyphenChars, hyphenLang,
                                base)
        if numberingStyle is not None: self.numberingStyle = numberingStyle
        if numberingSeparator is not None: self.numberingSeparator = numberingSeparator


HeadingStyle.default = []
HeadingStyle.default.append(HeadingStyle(base=ParagraphStyle.default,
                                    numberingStyle=NumberingStyle.number,
                                    numberingSeparator='.'))

class Heading(Paragraph):
    nextNumber = {}

    def __init__(self, level, title, style=None):
        if style is None:
            style = HeadingStyle.default
        if level in Heading.nextNumber:
            self._number = Heading.nextNumber[level]
            Heading.nextNumber[level] += 1
            Heading.nextNumber[level+1] = 1
        else:
            self._number = 1
            Heading.nextNumber[level] = 2
        self.level = level
        Paragraph.__init__(self, self._formatNumber(style[level - 1]) + ". " + title, style[level - 1])

    def _formatNumber(self, style):
##        style = self.style.numberingStyle
        style = style.numberingStyle
        if style == NumberingStyle.number:
            return str(self._number)
        elif style == NumberingStyle.character:
            string = ''
            while number > 26:
                number, remainder = divmod(number, 26)
                if remainder == 0:
                    remainder = 26
                    number -= 1
                string = chr(ord('a') - 1 + remainder) + string
            return chr(ord('a') - 1 + int(number)) + string
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
            (k, n) = divmod(n, num)
            roman.append(ltr * k)
        return "".join(roman)


class ListStyle(ParagraphStyle):
    def __init__(self, name="", indentLeft=None, indentRight=None, indentFirst=None,
                 spaceAbove=None, spaceBelow=None,
                 lineSpacing=None,
                 justify=None,
                 typeface=None, fontStyle=None, fontSize=None, smallCaps=None,
                 hyphenate=None, hyphenChars=None, hyphenLang=None,
                 ordered=False, itemSpacing=None,
                 base=None):
        ParagraphStyle.__init__(self, name, indentLeft, indentRight, indentFirst,
                                 spaceAbove, spaceBelow,
                                 lineSpacing,
                                 justify,
                                 typeface, fontStyle, fontSize, smallCaps,
                                 hyphenate, hyphenChars, hyphenLang,
                                 base)
        if ordered is not None: self.ordered = ordered
        if itemSpacing is not None: self.itemSpacing = itemSpacing


class List(Paragraph, list):
    def __init__(self, style=None):
        if style is None:
            style = ListStyle.default

        Paragraph.__init__(self, "", style)
        list.__init__(self)
        self.currentNumber = 1

    def __lshift__(self, listItem):
        self.append(listItem)

    def append(self, listItem):
##        assert isinstance(listItem, ListItem)
        list.append(self, "{}.&nbsp;".format(self.currentNumber) + listItem)
##        listItem.number = self.currentNumber
        self.currentNumber += 1

    def typeset(self, pscanvas, offset=0):
        normalItemStyle = ParagraphStyle("normal list item",
             spaceAbove=nil,
             spaceBelow=self.style.itemSpacing,
             base=self.style)
        lastItemStyle = ParagraphStyle("last list item",
             spaceAbove=nil,
             spaceBelow=self.style.spaceBelow,
             base=self.style)

        for i, item in enumerate(self):
            if i == len(self) - 1:
                itemStyle = lastItemStyle
            else:
                itemStyle = normalItemStyle

            itemParagraph = Paragraph(item, itemStyle)
            offset += itemParagraph.typeset(pscanvas, offset)

        return offset


### TODO: create common superclass for Heading and ListItem
##class ListItem(Paragraph):
##    def __init__(self, text):
##        Paragraph.__init__(self, text)
