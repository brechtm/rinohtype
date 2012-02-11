
from warnings import warn

from .layout import EndOfContainer
from .number import format_number
from .number.style import NUMBER
from .paragraph import ParagraphStyle, Paragraph
from .reference import Reference, Referenceable, REFERENCE, TITLE, PAGE
from .text import StyledText, FixedWidthSpace, Tab
from .unit import nil
from .warnings import PyteWarning


class HeadingStyle(ParagraphStyle):
    attributes = {'numberingStyle': NUMBER,
                  'numberingSeparator': '.'}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


# TODO: share superclass with List (numbering)
class Heading(Paragraph, Referenceable):
    style_class = HeadingStyle

    def __init__(self, document, title, style=None, level=1, id=None):
        self._title = title
        next_number = document.counters.setdefault(self.__class__, {1: 1})
        if style.numberingStyle is not None:
            self.number = format_number(next_number[level], style.numberingStyle)
            number = self.number + style.numberingSeparator + FixedWidthSpace()
            if level in next_number:
                next_number[level] += 1
                next_number[level + 1] = 1
            else:
                next_number[level] = 2
        else:
            self.number = None
            number = ""
        self.level = level
        if id is None:
            # an ID is necessary for building the TOC
            id = __builtins__['id'](self)
        Paragraph.__init__(self, number + title, style)
        Referenceable.__init__(self, document, id)

    def reference(self):
        return self.number

    def title(self):
        return self._title


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
            item = Paragraph("{}{}".format(i + 1, separator) +
                             FixedWidthSpace() + item,
                             style=item_style)
            self.append(item)
        self.append(Paragraph("{}{}".format(len(items), separator) +
                              FixedWidthSpace() + items[-1],
                              style=last_item_style))
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
            except EndOfContainer:
                self.itempointer = i
                raise

        self.itempointer = 0
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

    def __init__(self, style=None):
        super().__init__([], style)

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

    def __init__(self, style=None):
        super().__init__([], style)

    def typeset(self, pscanvas, offset=0):
        text = StyledText('{}'.format(self.page.number))
        text.parent = self
        self.append(text)
        return super().typeset(pscanvas, offset)


class TableOfContentsStyle(ParagraphStyle):
    attributes = {'depth': 3}

    def __init__(self, name, base=None, **attributes):
        super().__init__(name, base=base, **attributes)


class TableOfContents(Paragraph):
    style_class = TableOfContentsStyle

    def __init__(self, style=None, styles=[]):
        super().__init__([], style)
        self.styles = styles
        self.item_pointer = 0

    def register(self, flowable):
        if (isinstance(flowable, Heading) and
            flowable.level <= self.get_style('depth')):
            text = [Reference(flowable.id, type=REFERENCE), Tab(),
                    Reference(flowable.id, type=TITLE), Tab(),
                    Reference(flowable.id, type=PAGE)]
            try:
                style_index = flowable.level - 1
                flowable = Paragraph(text, style=self.styles[style_index])
            except AttributeError:
                flowable = Paragraph(text, style=self.styles[-1])
            flowable.parent = self
            self.append(flowable)

    def typeset(self, canvas, offset=0):
        offset_begin = offset
        while self.item_pointer < len(self):
            self.item_pointer += 1
            try:
                item = self[self.item_pointer - 1]
                offset += item.typeset(canvas, offset)
            except EndOfContainer:
                raise

        self.item_pointer = 0
        return offset - offset_begin
