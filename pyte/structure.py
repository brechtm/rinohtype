
from warnings import warn

from psg.exceptions import EndOfBox

from .text import StyledText
from .paragraph import ParagraphStyle, Paragraph
from .unit import nil
from .number import format_number
from .number.style import NUMBER
from .warnings import PyteWarning


class HeadingStyle(ParagraphStyle):
    attributes = {'numberingStyle': NUMBER,
                  'numberingSeparator': '.'}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class Referenceable(object):
    def __init__(self, id):
        self.id = id

    def reference(self):
        return self.ref


# TODO: share superclass with List (numbering)
class Heading(Paragraph):
    style_class = HeadingStyle

    next_number = {1: 1}

    def __init__(self, title, style=None, level=1):
        if style.numberingStyle is not None:
            self.ref = format_number(self.next_number[level],
                                     style.numberingStyle)
            number = self.ref + style.numberingSeparator + '&nbsp;'
        else:
            self.ref = None
            number = ""
        if level in self.next_number:
            self.next_number[level] += 1
            self.next_number[level + 1] = 1
        else:
            self.next_number[level] = 2
        self.level = level
        super().__init__(number + title, style)

    def reference(self):
        return self.ref


class ListStyle(ParagraphStyle):
    attributes = {'ordered': False,
                  'itemSpacing': ParagraphStyle.attributes['lineSpacing'],
                  'numberingStyle': NUMBER,
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


class HeaderStyle(ParagraphStyle):
    attributes = {}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class Header(Paragraph):
    style_class = HeaderStyle

    def __init__(self, page, style=None):
        super().__init__([], style)
        self.page = page

    def typeset(self, pscanvas, offset=0):
        text = StyledText('page number = {}'.format(self.page.number))
        text.parent = self
        self.append(text)
        return super().typeset(pscanvas, offset)


class FooterStyle(ParagraphStyle):
    attributes = {}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class Footer(Paragraph):
    style_class = FooterStyle

    def __init__(self, page, style=None):
        super().__init__([], style)
        self.page = page

    def typeset(self, pscanvas, offset=0):
        text = StyledText('{}'.format(self.page.number))
        text.parent = self
        self.append(text)
        return super().typeset(pscanvas, offset)



class Reference(StyledText):
    def __init__(self, id, target):
        super().__init__('')
        self.id = id
        self.document = target.document

    def characters(self):
        try:
            self.text = self.document.elements[self.id].reference()
        except KeyError:
            warn("Unknown label '{}'".format(self.id), PyteWarning)
            self.text = "unkown reference '{}'".format(self.id)
        if self.text is None:
            warn('Trying to reference unreferenceable object', PyteWarning)
            self.text = '[not referenceable]'
        for character in super().characters():
            yield character
