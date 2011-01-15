
from pyte.paragraph import ParagraphStyle, Paragraph, MixedStyledText
from pyte.unit import nil
from psg.exceptions import EndOfBox


class NumberingStyle:
    number = 0
    character = 1
    Character = 2
    roman = 3
    Roman = 4


class HeadingStyle(ParagraphStyle):
    attributes = {'numberingStyle': NumberingStyle.number,
                  'numberingSeparator': '.'}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


# TODO: share subclass with List (numbering)
class Heading(Paragraph):
    style_class = HeadingStyle

    next_number = {1: 1}

    def __init__(self, title, style=None, level=1):
        if style.numberingStyle:
            number = self._format_number(self.next_number[level], style) + ". "
        else:
            number = ""
        if level in self.next_number:
            self.next_number[level] += 1
            self.next_number[level + 1] = 1
        else:
            self.next_number[level] = 2
        self.level = level
        super().__init__(number + title, style)


    @classmethod
    def _format_number(cls, number, style):
        style = style.numberingStyle
        if style == NumberingStyle.number:
            return str(number)
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
            return chr(ord('A') - 1 + number)
        elif style == NumberingStyle.roman:
            return cls._romanize(number).lower()
        elif style == NumberingStyle.Roman:
            return cls._romanize(number)

    @classmethod
    def _romanize(cls, n):
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
    attributes = {'ordered': False,
                  'itemSpacing': ParagraphStyle.attributes['lineSpacing'],
                  'numberingStyle': NumberingStyle.number,
                  'numberingSeparator': ')'}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class List(Paragraph):
    style_class = ListStyle

    def __init__(self, items, style=None):
        super().__init__([], style)
        item_style = ParagraphStyle("list item",
                                    spaceAbove=nil,
                                    spaceBelow=style.itemSpacing,
                                    base=style)
        last_item_style = ParagraphStyle("last list item",
                                         spaceAbove=nil,
                                         spaceBelow=style.spaceBelow,
                                         base=style)
        separator = style.numberingSeparator
        for i, item in enumerate(items[:-1]):
            item = Paragraph("{}{}&nbsp;".format(i + 1, separator) + item,
                             style=item_style)
            self.append(item)
        self.append(Paragraph("{}{}&nbsp;".format(len(items), separator) +
                              items[-1], style=last_item_style))
        self.itempointer = 0

##    def append(self, listItem):
####        assert isinstance(listItem, ListItem)
##        item_par = Paragraph("{}.&nbsp;".format(self.currentNumber) + listItem,
##                             self.itemStyle)
##        list.append(self, item_par)
####        listItem.number = self.currentNumber
##        self.currentNumber += 1

    def typeset(self, pscanvas, offset=0):
        offset_begin = offset
        #for i, item in enumerate(self):
        for i in range(self.itempointer, len(self)):
            try:
                item = self[i]
                offset += item.typeset(pscanvas, offset)
            except EndOfBox:
                self.itempointer = i
                raise

        return offset - offset_begin


### TODO: create common superclass for Heading and ListItem
##class ListItem(Paragraph):
##    def __init__(self, text):
##        Paragraph.__init__(self, text)
