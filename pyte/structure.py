
import unicodedata

from .layout import EndOfContainer
from .number import format_number, NUMBER
from .paragraph import ParagraphStyle, Paragraph
from .reference import Reference, Referenceable, REFERENCE, TITLE, PAGE
from .reference import Variable, PAGE_NUMBER, NUMBER_OF_PAGES
from .reference import SECTION_NUMBER, SECTION_TITLE
from .text import SingleStyledText, FixedWidthSpace, Tab
from .dimension import PT
from .style import PARENT_STYLE
from .warnings import PyteWarning


class HeadingStyle(ParagraphStyle):
    attributes = {'numbering_style': NUMBER,
                  'numbering_separator': '.'}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


# TODO: share superclass with List (numbering)
class Heading(Paragraph, Referenceable):
    style_class = HeadingStyle

    def __init__(self, document, title, style=None, level=1, id=None):
        self._title = title
        counters = document.counters.setdefault(self.__class__, {1: 1})
        if style.numbering_style is not None:
            self.number = format_number(counters[level], style.numbering_style)
            number = self.number + style.numbering_separator + FixedWidthSpace()
            counters[level] += 1
            counters[level + 1] = 1
        else:
            self.number = None
            number = ''
        self.level = level
        if id is None:
            id = document.unique_id
        Paragraph.__init__(self, number + title, style)
        Referenceable.__init__(self, document, id)

    def reference(self):
        return self.number

    def title(self):
        return self._title

    def render(self, container):
        if self.level == 1:
            container.page.section = self
        self.update_page_reference(container.page)
        return super().render(container)


class ListStyle(ParagraphStyle):
    attributes = {'ordered': False,
                  'bullet': SingleStyledText('\N{BULLET}'),
                  'item_spacing': ParagraphStyle.attributes['line_spacing'],
                  'numbering_style': NUMBER,
                  'numbering_separator': ')'}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class List(Paragraph):
    style_class = ListStyle

    def __init__(self, items, style=None):
        super().__init__([], style)
        item_style = ParagraphStyle(space_above=0*PT,
                                    space_below=self.style.item_spacing,
                                    base=style)
        last_item_style = ParagraphStyle(space_above=0*PT,
                                         space_below=0*PT,
                                         base=style)
        if style.ordered:
            separator = style.numbering_separator
            numbers = [format_number(i + 1, self.get_style('numbering_style'))
                       for i in range(len(items))]
        else:
            separator = ''
            numbers = [style.bullet] * len(items)
        for i, item in enumerate(items[:-1]):
            item = Paragraph(numbers[i] + separator + FixedWidthSpace() + item,
                             style=item_style)
            item.parent = self
            self.append(item)
        last = Paragraph(numbers[-1] + separator + FixedWidthSpace() + items[-1],
                         style=last_item_style)
        last.parent = self
        self.append(last)
        self.item_pointer = 0

##    def append(self, listItem):
####        assert isinstance(listItem, ListItem)
##        item_par = Paragraph("{}.&nbsp;".format(self.currentNumber) + listItem,
##                             self.itemStyle)
##        list.append(self, item_par)
####        listItem.number = self.currentNumber
##        self.currentNumber += 1

    def typeset(self, container):
        while self.item_pointer < len(self):
            item = self[self.item_pointer]
            item.flow(container)
            self.item_pointer += 1
        self.item_pointer = 0


### TODO: create common superclass for Heading and ListItem
##class ListItem(Paragraph):
##    def __init__(self, text):
##        Paragraph.__init__(self, text)


class DefinitionListStyle(ParagraphStyle):
    attributes = {'term_style': PARENT_STYLE,
                  'item_spacing': ParagraphStyle.attributes['line_spacing'],
                  'indentation': 10*PT}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class DefinitionList(Paragraph):
    style_class = DefinitionListStyle

    def __init__(self, items, style=None):
        super().__init__([], style)
        term_style = self.style.term_style
        term_style = ParagraphStyle(space_above=0*PT,
                                    space_below=0*PT,
                                    base=style)
        definition_style = ParagraphStyle(space_above=0*PT,
                                          space_below=self.style.item_spacing,
                                          indent_left=self.style.indentation,
                                          base=style)
        last_definition_style = ParagraphStyle(space_above=0*PT,
                                               space_below=0*PT,
                                               indent_left=self.style.indentation,
                                               base=style)
        for i, item in enumerate(items[:-1]):
            term, definition = item
            term_par = Paragraph(term, style=term_style)
            definition_par =  Paragraph(definition, style=definition_style)
            term_par.parent = definition_par.parent = self
            self.append(term_par)
            self.append(definition_par)
        last_term, last_definition = items[-1]
        last_term_par = Paragraph(last_term, style=term_style)
        last_definition_par = Paragraph(last_definition,
                                        style=last_definition_style)
        last_term_par.parent = last_definition_par.parent = self
        self.append(last_term_par)
        self.append(last_definition_par)
        self.item_pointer = 0

    def typeset(self, container):
        while self.item_pointer < len(self):
            item = self[self.item_pointer]
            item.flow(container)
            self.item_pointer += 1
        self.item_pointer = 0


class HeaderStyle(ParagraphStyle):
    attributes = {}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Header(Paragraph):
    style_class = HeaderStyle

    def __init__(self, style=None):
        super().__init__([], style)

    def typeset(self, container):
        text = Variable(SECTION_NUMBER) + ' ' + Variable(SECTION_TITLE)
        text.parent = self
        self.append(text)
        return super().typeset(container)


class FooterStyle(ParagraphStyle):
    attributes = {}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class Footer(Paragraph):
    style_class = FooterStyle

    def __init__(self, style=None):
        super().__init__([], style)

    def typeset(self, container):
        text = Variable(PAGE_NUMBER) + ' / ' + Variable(NUMBER_OF_PAGES)
        text.parent = self
        self.append(text)
        return super().typeset(container)


class TableOfContentsStyle(ParagraphStyle):
    attributes = {'depth': 3}

    def __init__(self, base=None, **attributes):
        super().__init__(base=base, **attributes)


class TableOfContents(Paragraph):
    style_class = TableOfContentsStyle
    location = 'table of contents'

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
            for reference in text:
                reference.source = self
            try:
                style_index = flowable.level - 1
                flowable = Paragraph(text, style=self.styles[style_index])
            except AttributeError:
                flowable = Paragraph(text, style=self.styles[-1])
            flowable.parent = self
            self.append(flowable)

    def typeset(self, container):
        offset_begin = container.cursor
        while self.item_pointer < len(self):
            self.item_pointer += 1
            try:
                item = self[self.item_pointer - 1]
                item.flow(container)
            except EndOfContainer:
                raise

        self.item_pointer = 0
        return container.cursor - offset_begin
